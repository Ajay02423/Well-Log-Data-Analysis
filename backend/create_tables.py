from app.db.session import engine
from app.db.base import Base

import app.models.well
import app.models.curve

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
