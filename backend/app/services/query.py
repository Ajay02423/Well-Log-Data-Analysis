from collections import defaultdict
from typing import Dict, List
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.curve import Curve, CurveData
from sqlalchemy.orm import Session
from app.models.curve import CurveData, Curve
from sqlalchemy import func


def safe_float(value):
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value

def query_depth_range(
    db: Session,
    well_id: str,
    curve_names: List[str],
    min_depth: float,
    max_depth: float,
) -> Dict:
    """
    Returns depth-aligned curve data for the given curves and depth range.
    """

    # Fetch curves for this well
    curves = (
        db.query(Curve)
        .filter(
            Curve.well_id == well_id,
            Curve.name.in_(curve_names),
        )
        .all()
    )

    if not curves:
        return {"depths": [], "curves": {}}

    curve_id_to_name = {c.id: c.name for c in curves}

    # Query curve data in range
    rows = (
        db.query(CurveData.curve_id, CurveData.depth, CurveData.value)
        .filter(
            CurveData.curve_id.in_(curve_id_to_name.keys()),
            and_(
                CurveData.depth >= min_depth,
                CurveData.depth <= max_depth,
            ),
        )
        .order_by(CurveData.depth)
        .all()
    )

    # Organize by depth
    depth_map: Dict[float, Dict[str, float | None]] = defaultdict(dict)

    for curve_id, depth, value in rows:
        curve_name = curve_id_to_name[curve_id]
        depth_map[float(depth)][curve_name] = value

    depths = sorted(depth_map.keys())

    # Build aligned arrays
    result_curves: Dict[str, List[float | None]] = {}
    for name in curve_names:
        result_curves[name] = [
            safe_float(depth_map[d].get(name)) for d in depths
        ]

    return {
        "depths": depths,
        "curves": result_curves,
    }


def get_depth_range(db: Session, well_id: str):
    result = (
        db.query(
            func.min(CurveData.depth),
            func.max(CurveData.depth),
        )
        .join(Curve, Curve.id == CurveData.curve_id)
        .filter(Curve.well_id == well_id)
        .one()
    )

    min_depth, max_depth = result

    if min_depth is None or max_depth is None:
        return None

    return {
        "min_depth": float(min_depth),
        "max_depth": float(max_depth),
    }
