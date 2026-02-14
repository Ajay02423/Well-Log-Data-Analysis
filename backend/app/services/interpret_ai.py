import numpy as np
from sqlalchemy.orm import Session
from app.models.curve import Curve, CurveData


def interpret_structured(
    db: Session,
    well_id: str,
    curves: list[str],
    min_depth: float,
    max_depth: float,
):
    """
    Pure numerical / statistical interpretation (NO LLM here).
    Returns deterministic statistics for selected curves.
    """

    results = []

    for curve_name in curves:
        curve = (
            db.query(Curve)
            .filter(
                Curve.well_id == well_id,
                Curve.name == curve_name,
            )
            .first()
        )

        if not curve:
            continue

        rows = (
            db.query(CurveData.depth, CurveData.value)
            .filter(
                CurveData.curve_id == curve.id,
                CurveData.depth >= min_depth,
                CurveData.depth <= max_depth,
                CurveData.value.isnot(None),
            )
            .order_by(CurveData.depth)
            .all()
        )

        # Filter finite values ONCE
        filtered = [
            (d, v) for d, v in rows
            if np.isfinite(v)
        ]

        if len(filtered) < 10:
            continue

        depths = np.array([d for d, _ in filtered])
        vals   = np.array([v for _, v in filtered])

        # Basic statistics
        mean = float(np.mean(vals))
        std  = float(np.std(vals))
        vmin = float(np.min(vals))
        vmax = float(np.max(vals))

        # Normalize depth for stable slope
        depth_norm = depths - depths.mean()
        slope = np.polyfit(depth_norm, vals, 1)[0]

        # Relative trend detection
        slope_threshold = 0.01 * (vmax - vmin) / (max_depth - min_depth)

        if abs(slope) < slope_threshold:
            trend = "flat"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        results.append(
            {
                "curve": curve_name,
                "samples": len(vals),
                "mean": round(mean, 3),
                "std": round(std, 3),
                "min": round(vmin, 3),
                "max": round(vmax, 3),
                "range": round(vmax - vmin, 3),
                "trend": trend,
            }
        )

    return {
        "depth_range": {
            "min": min_depth,
            "max": max_depth,
            "unit": "ft",
        },
        "curve_insights": results,
    }
