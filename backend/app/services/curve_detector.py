from app.models.curve import Curve

def detect_curves(db, well_id: str, question: str):
    curves = (
        db.query(Curve.name)
        .filter(Curve.well_id == well_id)
        .all()
    )
    curve_names = [c[0] for c in curves]

    detected = []
    q = question.upper()

    for name in curve_names:
        if name in q:
            detected.append(name)

    return detected
