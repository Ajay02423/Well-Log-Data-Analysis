import uuid
import tempfile
import numpy as np
import pandas as pd
import lasio
from sqlalchemy.orm import Session
from app.models.well import Well
from app.models.curve import Curve, CurveData
from app.services.s3 import get_s3_client, upload_file
from app.core.config import settings
from app.db.session import SessionLocal

SKIP_CURVES = ["DEPT", "DEPTH", "TIME"]

# 🚀 INCREASED BATCH SIZE
# 10k -> 50k reduces DB roundtrips from ~156 to ~31 for your dataset.
BATCH_SIZE = 50000 

def parse_and_store_las(s3_key: str, well_id, db: Session):
    s3 = get_s3_client()

    # ===============================
    # 1️⃣ Download & Read LAS
    # ===============================
    with tempfile.NamedTemporaryFile(suffix=".las") as tmp:
        s3.download_file(settings.S3_BUCKET_NAME, s3_key, tmp.name)
        las = lasio.read(tmp.name)

    df = las.df()
    
    # Fast replacement of NULLs
    df = df.replace([las.well.NULL.value], np.nan)
    df = df.rename_axis("DEPTH").reset_index()

    # Update Well Metadata
    well = db.query(Well).filter(Well.id == well_id).first()
    well.min_depth = float(df["DEPTH"].min())
    well.max_depth = float(df["DEPTH"].max())
    
    valid_columns = [
        col for col in df.columns 
        if col.upper() not in SKIP_CURVES and col != "DEPTH"
    ]
    
    well.total_curves = len(valid_columns)
    well.processed_curves = 0
    db.commit()

    # ===============================
    # 2️⃣ Create Curve Metadata
    # ===============================
    # Pre-calculate curve objects
    curves_to_add = []
    
    # ⚡ Optimization: Filter columns with all NaNs before creating objects
    # This prevents creating curves that have no data
    df_clean = df.dropna(axis=1, how='all')
    valid_columns = [c for c in valid_columns if c in df_clean.columns]

    for col_name in valid_columns:
        unit = las.curves[col_name].unit if col_name in las.curves else ""
        curves_to_add.append(Curve(well_id=well_id, name=col_name, unit=unit))

    if not curves_to_add:
        well.is_ready = True
        well.progress = 100
        db.commit()
        return

    db.add_all(curves_to_add)
    db.flush() # Get IDs

    curve_name_to_id = {c.name: c.id for c in curves_to_add}

    # ===============================
    # 3️⃣ Prepare Data (Vectorized Melt)
    # ===============================
    df_long = df.melt(
        id_vars=["DEPTH"], 
        value_vars=[c.name for c in curves_to_add],
        var_name="curve_name", 
        value_name="value"
    )

    df_long = df_long.dropna(subset=["value"])
    
    # Map IDs
    df_long["curve_id"] = df_long["curve_name"].map(curve_name_to_id)
    df_long = df_long.rename(columns={"DEPTH": "depth"})
    
    # ⚡ Optimization: Keep it as a DataFrame. 
    # Do NOT convert to_dict('records') here. It consumes too much RAM.
    final_df = df_long[["curve_id", "depth", "value"]]
    
    total_rows = len(final_df)
    
    # ===============================
    # 4️⃣ Batch Insert (Memory Optimized)
    # ===============================
    for i in range(0, total_rows, BATCH_SIZE):
        # 1. Slice the DataFrame (Cheap operation)
        chunk = final_df.iloc[i : i + BATCH_SIZE]
        
        # 2. Convert ONLY this chunk to dicts (Saves RAM)
        batch = chunk.to_dict("records")
        
        # 3. Insert
        db.bulk_insert_mappings(CurveData, batch)
        
        # 4. Update Progress
        # Calculate percentage
        progress_pct = int(((i + BATCH_SIZE) / total_rows) * 100)
        if progress_pct > 100: progress_pct = 99

        # Only touch the 'well' table every few loops to prevent locking
        if progress_pct % 10 == 0 or i + BATCH_SIZE >= total_rows:
            well.progress = progress_pct
            well.processed_curves = int((progress_pct / 100) * well.total_curves)
            db.commit()
        else:
            # Commit the inserts to free up DB transaction log
            db.commit()

    # ===============================
    # 5️⃣ Finalize
    # ===============================
    well.progress = 100
    well.processed_curves = well.total_curves
    well.is_ready = True
    db.commit()

# ... (Keep existing ingest_las_file and ingest_las_background helpers) ...
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
    finally:
        db.close()