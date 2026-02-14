import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Curve(Base):
    __tablename__ = "curves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    well_id = Column(UUID(as_uuid=True), ForeignKey("wells.id"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=True)

    well = relationship("Well", back_populates="curves")
    data = relationship("CurveData", back_populates="curve", cascade="all, delete")


class CurveData(Base):
    __tablename__ = "curve_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curve_id = Column(UUID(as_uuid=True), ForeignKey("curves.id"), nullable=False)
    depth = Column(Float, nullable=False)
    value = Column(Float, nullable=True)

    curve = relationship("Curve", back_populates="data")


Index("idx_curve_depth", CurveData.curve_id, CurveData.depth)
