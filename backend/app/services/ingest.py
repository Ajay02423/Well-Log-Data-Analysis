import uuid
import tempfile
import numpy as np
import pandas as pd
import lasio
import io
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.well import Well
from app.models.curve import Curve, CurveData
from app.services.s3 import get_s3_client, upload_file
from app.core.config import settings
from app.db.session import SessionLocal

SKIP_CURVES = ["DEPT", "DEPTH", "TIME"]

def fast_insert_postgres(db: Session, df_data: pd.DataFrame, table_name: str):
    """
    Uses the Postgres COPY protocol to insert data at maximum speed.
    """
    # 1. Get the raw DBAPI connection (psycopg2)
    # SQLAlchemy wraps it, so we dig inside
    conn = db.connection().connection
    
    # 2. Create an in-memory CSV buffer
    output = io.StringIO()
    
    # 3. Write DataFrame to CSV format (No index, No header)
    # Ensure columns match DB order: curve_id, depth, value
    df_data[['curve_id', 'depth', 'value']].to_csv(
        output, 
        sep=',', 
        header=False, 
        index=False
    )
    output.seek(0)
    
    # 4. Run the COPY command
    # This bypasses the ORM and SQL parsing layer entirely
    cursor = conn.cursor()
    try:
        cursor.copy_expert(
            f"COPY {table_name} (curve_id, depth, value) FROM STDIN WITH (FORMAT CSV)",
            output
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def parse_and_store_las(s3_key: str, well_id, db: Session):
    s3 = get_s3_client()

    # ===============================
    # 1️⃣ Download & Read LAS
    # ===============================
    with tempfile.NamedTemporaryFile(suffix=".las") as tmp:
        s3.download_file(settings.S3_BUCKET_NAME, s3_key, tmp.name)
        las = lasio.read(tmp.name)

    df = las.df()
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
    well.progress = 5  # Mark as started
    db.commit()

    # ===============================
    # 2️⃣ Create Curve Metadata
    # ===============================
    curve_name_to_id = {}
    curves_to_add = []
    
    for col_name in valid_columns:
        if df[col_name].isna().all():
            continue
        
        # Use existing unit or empty
        unit = las.curves[col_name].unit if col_name in las.curves else ""
        
        curves_to_add.append(
            Curve(well_id=well_id, name=col_name, unit=unit)
        )

    if not curves_to_add:
        well.is_ready = True
        well.progress = 100
        db.commit()
        return

    db.add_all(curves_to_add)
    db.commit() # Commit to get IDs

    for c in curves_to_add:
        curve_name_to_id[c.name] = c.id

    # ===============================
    # 3️⃣ Prepare Data (Vectorized)
    # ===============================
    df_long = df.melt(
        id_vars=["DEPTH"], 
        value_vars=[c.name for c in curves_to_add],
        var_name="curve_name", 
        value_name="value"
    )
    
    df_long = df_long.dropna(subset=["value"])
    df_long["curve_id"] = df_long["curve_name"].map(curve_name_to_id)
    df_long = df_long.rename(columns={"DEPTH": "depth"})
    
    # Final dataframe for insertion
    final_df = df_long[["curve_id", "depth", "value"]]

    # ===============================
    # 4️⃣ Insert Data (Fast Path)
    # ===============================
    total_rows = len(final_df)
    
    # Split into 5 chunks so the progress bar updates
    # If file is small, np.array_split handles it gracefully
    chunks = np.array_split(final_df, 5) 
    
    try:
        # Check if table name is 'curve_data' or other
        # Using the model's __tablename__ ensures we are correct
        table_name = CurveData.__tablename__
        
        for i, chunk in enumerate(chunks):
            if chunk.empty:
                continue
                
            # Run the ULTRA FAST COPY command
            fast_insert_postgres(db, chunk, table_name)
            
            # Update Progress
            progress = int(((i + 1) / len(chunks)) * 100)
            
            # Ensure we don't accidentally set it to 100 before finishing
            if progress >= 100: progress = 99 
            
            well.progress = progress
            well.processed_curves = int((progress / 100) * well.total_curves)
            db.commit()
            
    except Exception as e:
        print(f"❌ Fast Insert Failed: {e}")
        print("⚠️ Falling back to slow Insert...")
        
        # Fallback for SQLite or if COPY fails
        # Convert to dictionary (Slower)
        data_dicts = final_df.to_dict("records")
        BATCH_SIZE = 5000
        for i in range(0, len(data_dicts), BATCH_SIZE):
            batch = data_dicts[i : i + BATCH_SIZE]
            db.bulk_insert_mappings(CurveData, batch)
            db.commit()

    # ===============================
    # 5️⃣ Finalize
    # ===============================
    well.progress = 100
    well.processed_curves = well.total_curves
    well.is_ready = True
    db.commit()


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