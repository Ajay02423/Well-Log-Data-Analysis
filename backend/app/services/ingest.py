import uuid
import tempfile
import numpy as np
import pandas as pd
import lasio
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.well import Well
from app.models.curve import Curve, CurveData
from app.services.s3 import get_s3_client, upload_file
from app.core.config import settings
from app.db.session import SessionLocal

SKIP_CURVES = ["DEPT", "DEPTH", "TIME"]
BATCH_SIZE = 10000  # Increased batch size for speed

def parse_and_store_las(s3_key: str, well_id, db: Session):
    s3 = get_s3_client()

    # ===============================
    # 1️⃣ Download & Read LAS (Fast)
    # ===============================
    with tempfile.NamedTemporaryFile(suffix=".las") as tmp:
        s3.download_file(settings.S3_BUCKET_NAME, s3_key, tmp.name)
        # read_policy='default' is faster usually
        las = lasio.read(tmp.name)

    # Convert to Pandas DataFrame immediately (Much faster than iterating)
    df = las.df()
    
    # Clean up standard null values (Lasio usually handles this, but safety first)
    df = df.replace([las.well.NULL.value], np.nan)

    # Get depth column (index) into the dataframe as a column
    df = df.rename_axis("DEPTH").reset_index()

    # Update Well Metadata
    well = db.query(Well).filter(Well.id == well_id).first()
    well.min_depth = float(df["DEPTH"].min())
    well.max_depth = float(df["DEPTH"].max())
    
    # Identify valid curves (columns that are not depth and not in skip list)
    valid_columns = [
        col for col in df.columns 
        if col.upper() not in SKIP_CURVES 
        and col != "DEPTH"
    ]
    
    well.total_curves = len(valid_columns)
    well.processed_curves = 0
    db.commit()

    # ===============================
    # 2️⃣ Create Curve Metadata
    # ===============================
    # Create all Curve objects first to get their IDs
    curve_name_to_id = {}
    
    curves_to_add = []
    for col_name in valid_columns:
        # Check if column has actual data (not all NaNs)
        if df[col_name].isna().all():
            continue
            
        unit = las.curves[col_name].unit if col_name in las.curves else ""
        curve_obj = Curve(
            well_id=well_id,
            name=col_name,
            unit=unit
        )
        curves_to_add.append(curve_obj)

    if not curves_to_add:
        well.is_ready = True
        well.progress = 100
        db.commit()
        return

    db.add_all(curves_to_add)
    db.flush() # Generates IDs without committing transaction

    # Create a map: {'GR': 5, 'RES': 6}
    for c in curves_to_add:
        curve_name_to_id[c.name] = c.id

    # ===============================
    # 3️⃣ Prepare Data (Vectorized Melt)
    # ===============================
    # This turns Wide format (Depth, GR, RES) -> Long format (Depth, CurveName, Value)
    # This is 100x faster than a Python for-loop
    df_long = df.melt(
        id_vars=["DEPTH"], 
        value_vars=[c.name for c in curves_to_add],
        var_name="curve_name", 
        value_name="value"
    )

    # Remove NaNs to save DB space
    df_long = df_long.dropna(subset=["value"])

    # Map curve names to IDs
    # We use map() which is very fast in Pandas
    df_long["curve_id"] = df_long["curve_name"].map(curve_name_to_id)

    # Rename columns to match SQLAlchemy model
    df_long = df_long.rename(columns={"DEPTH": "depth"})
    
    # Keep only relevant columns
    final_data = df_long[["curve_id", "depth", "value"]].to_dict("records")

    total_rows = len(final_data)
    
    # ===============================
    # 4️⃣ Batch Insert
    # ===============================
    # Insert in chunks of 10,000
    for i in range(0, total_rows, BATCH_SIZE):
        batch = final_data[i : i + BATCH_SIZE]
        db.bulk_insert_mappings(CurveData, batch)
        
        # Update progress based on ROWS inserted, not just curves
        # This makes the progress bar smoother
        progress_pct = int((i / total_rows) * 100)
        
        # Only update DB if progress changed significantly (every 5%)
        # to prevent locking the DB row constantly
        if progress_pct % 5 == 0:
            well.progress = progress_pct
            # Also update processed_curves roughly
            well.processed_curves = int((progress_pct / 100) * well.total_curves)
            db.commit()
        else:
            # Commit the data insert anyway to free up memory
            db.commit()

    # ===============================
    # 5️⃣ Finalize
    # ===============================
    well.progress = 100
    well.processed_curves = well.total_curves
    well.is_ready = True
    db.commit()


# Keep these helpers the same
def ingest_las_file(file, db: Session):
    s3_key = f"las/{uuid.uuid4()}.las"
    upload_file(file, s3_key)

    well = Well(
        s3_key=s3_key,
        is_ready=False,
        progress=0.0,
        processed_curves=0,
        total_curves=0,
    )
    db.add(well)
    db.commit()
    db.refresh(well)

    parse_and_store_las(s3_key, well.id, db)
    return well


def ingest_las_background(s3_key: str, well_id):
    db = SessionLocal()
    try:
        parse_and_store_las(s3_key, well_id, db)
    except Exception as e:
        print(f"Error processing LAS: {e}")
        # Optionally mark well as failed in DB
    finally:
        db.close()