import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Well(Base):
    __tablename__ = "wells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    s3_key = Column(String, nullable=False)
    
    total_curves = Column(Integer, default=0)
    processed_curves = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
     # 👇 REQUIRED FOR FRONTEND
    min_depth = Column(Float, nullable=True)
    max_depth = Column(Float, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_ready = Column(Boolean, default=False)
    curves = relationship("Curve", back_populates="well", cascade="all, delete")
