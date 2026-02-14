import uuid
import tempfile
import math
import lasio
from sqlalchemy.orm import Session

from app.models.well import Well
from app.models.curve import Curve, CurveData
from app.services.s3 import get_s3_client, upload_file
from app.core.config import settings
from app.db.session import SessionLocal


SKIP_CURVES = {"DEPT", "DEPTH", "TIME"}
MIN_VALID_POINTS = 100
BATCH_SIZE = 5000


def parse_and_store_las(s3_key: str, well_id, db: Session):
    s3 = get_s3_client()

    # ===============================
    # 1️⃣ Download LAS
    # ===============================
    with tempfile.NamedTemporaryFile() as tmp:
        s3.download_file(settings.S3_BUCKET_NAME, s3_key, tmp.name)
        las = lasio.read(tmp.name)

    depths = las.index
    null_value = las.well.NULL.value

    # ===============================
    # 2️⃣ Initialize well metadata
    # ===============================
    well = db.query(Well).filter(Well.id == well_id).first()

    well.min_depth = float(las.well.STRT.value)
    well.max_depth = float(las.well.STOP.value)

    valid_curves = [
        c for c in las.curves
        if c.mnemonic.strip().upper() not in SKIP_CURVES
    ]

    well.total_curves = len(valid_curves)
    well.processed_curves = 0
    well.progress = 0.0

    db.commit()

    # ===============================
    # 3️⃣ Ingest curves (FAST PATH)
    # ===============================
    with db.no_autoflush:
        for curve in valid_curves:
            mnemonic = curve.mnemonic.strip().upper()
            values = las[mnemonic]

            clean_values = [
                float(v)
                for v in values
                if v is not None
                and v != null_value
                and not math.isnan(v)
            ]

            # 🚫 Skip junk curves
            if len(clean_values) < MIN_VALID_POINTS:
                continue

            if max(clean_values) == min(clean_values):
                continue

            curve_obj = Curve(
                well_id=well_id,
                name=mnemonic,
                unit=curve.unit,
            )
            db.add(curve_obj)
            db.flush()  # get curve_obj.id

            rows = []

            for depth, value in zip(depths, values):
                rows.append(
                    {
                        "curve_id": curve_obj.id,
                        "depth": float(depth),
                        "value": None
                        if value in (None, null_value)
                        else float(value),
                    }
                )

                if len(rows) >= BATCH_SIZE:
                    db.bulk_insert_mappings(CurveData, rows)
                    rows.clear()

            if rows:
                db.bulk_insert_mappings(CurveData, rows)

            # ✔ Commit ONCE per curve
            db.commit()

            # ===============================
            # 4️⃣ Progress update
            # ===============================
            well.processed_curves += 1
            well.progress = (
                well.processed_curves / well.total_curves
            ) * 100.0
            db.commit()

    # ===============================
    # 5️⃣ Finalize well
    # ===============================
    well.progress = 100.0
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
    finally:
        db.close()
