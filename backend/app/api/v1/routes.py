from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import boto3
from app.core.config import settings


from app.db.session import get_db
from app.models.well import Well
from app.models.curve import Curve

from app.schemas.query import (
    DepthRangeRequest,
    DepthRangeResponse,
    DepthRangeInfo,
)

from app.services.s3 import upload_file
from app.services.ingest import ingest_las_background
from app.services.query import query_depth_range, get_depth_range

from app.services.interpret_ai import interpret_structured
from app.services.llm_helper import generate_interpretation_text
from app.schemas.interpret import InterpretRequest, InterpretResponse

router = APIRouter()

# ===============================
# List all wells
# ===============================
@router.get("/wells")
def list_wells(db: Session = Depends(get_db)):
    wells = db.query(Well).order_by(Well.id.desc()).all()

    return [
        {
            "id": str(w.id),
            "s3_key": w.s3_key,
            "is_ready": w.is_ready,
            "min_depth": w.min_depth,
            "max_depth": w.max_depth,
        }
        for w in wells
    ]


# ===============================
# Get single well status
# ===============================
@router.get("/wells/{well_id}")
def get_well(well_id: str, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()

    if not well:
        return None

    return {
        "id": str(well.id),
        "is_ready": well.is_ready,
        "min_depth": well.min_depth,
        "max_depth": well.max_depth,
    }


# ===============================
# List curves (ONLY when ready)
# ===============================
@router.get("/wells/{well_id}/curves")
def list_curves(well_id: str, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()

    # 🚨 Prevent partial ingestion reads
    if not well or not well.is_ready:
        return []

    curves = (
        db.query(Curve.name)
        .filter(Curve.well_id == well_id)
        .order_by(Curve.name)
        .all()
    )

    return [c[0] for c in curves]


# ===============================
# Depth range for a well
# ===============================
@router.get(
    "/wells/{well_id}/depth-range",
    response_model=DepthRangeInfo,
)
def get_well_depth_range(
    well_id: str,
    db: Session = Depends(get_db),
):
    result = get_depth_range(db, well_id)

    if result is None:
        return {"min_depth": 0, "max_depth": 0}

    return result


# ===============================
# Query curves by depth range
# ===============================
@router.post("/query", response_model=DepthRangeResponse)
def query_curves(
    req: DepthRangeRequest,
    db: Session = Depends(get_db),
):
    return query_depth_range(
        db,
        req.well_id,
        req.curves,
        req.min_depth,
        req.max_depth,
    )

@router.get("/wells/{well_id}/progress")
def get_progress(well_id: str, db: Session = Depends(get_db)):
    well = db.query(Well).filter(Well.id == well_id).first()

    if not well:
        return {"progress": 0}

    return {
        "progress": well.progress,
        "processed": well.processed_curves,
        "total": well.total_curves,
    }


@router.post("/interpret", response_model=InterpretResponse)
def interpret_api(
    body: InterpretRequest,
    db: Session = Depends(get_db),
):
    structured = interpret_structured(
        db,
        body.well_id,
        body.curves,
        body.min_depth,
        body.max_depth,
    )

    explanation = generate_interpretation_text(structured)

    return {
        "structured_insights": structured,
        "interpretation_text": explanation,
    }


from app.schemas.chat import ChatRequest, ChatResponse
from app.services.interpret_ai import interpret_structured
from app.services.llm_helper import generate_interpretation_text
from app.services.chat_llm import generate_chat_response
@router.post("/chat")
def chat_with_well(
    body: ChatRequest,
    db: Session = Depends(get_db),
):
    structured = None

    # Only compute stats if user provided well context (allow empty selected_curves)
    if (
        body.well_id
        and body.min_depth is not None
        and body.max_depth is not None
    ):
        curves = body.selected_curves or []

        # If no curves were selected by the user, use all curves for the well
        if not curves:
            curves = [c[0] for c in db.query(Curve.name).filter(Curve.well_id == body.well_id).order_by(Curve.name).all()]

        if curves:
            structured = interpret_structured(
                db=db,
                well_id=body.well_id,
                curves=curves,
                min_depth=body.min_depth,
                max_depth=body.max_depth,
            )

    answer, conv_id = generate_chat_response(
        question=body.question,
        structured_data=structured,
        selected_curves=body.selected_curves or [],
        conversation_id=body.conversation_id,
    )

    return {"answer": answer, "conversation_id": conv_id}

@router.post("/presign-upload")
def presign_upload(filename: str):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    s3_key = f"las/{uuid.uuid4()}-{filename}"

    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": "application/octet-stream",
        },
        ExpiresIn=300,  # 5 minutes
    )

    return {
        "upload_url": url,
        "s3_key": s3_key,
    }

@router.post("/confirm-upload")
def confirm_upload(
    s3_key: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    well = Well(
        s3_key=s3_key,
        is_ready=False,
    )
    db.add(well)
    db.commit()
    db.refresh(well)

    background_tasks.add_task(
        ingest_las_background,
        s3_key,
        well.id,
    )

    return {
        "well_id": str(well.id),
        "status": "processing",
    }
