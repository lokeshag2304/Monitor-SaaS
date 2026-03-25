from backend.database import SessionLocal
from backend.models.incident import Incident
import traceback

with open("crash.log", "w") as f:
    db = SessionLocal()
    try:
        incidents = db.query(Incident).limit(1).all()
        f.write(f"Success: {len(incidents)} incidents found\n")
    except Exception as e:
        f.write(f"Error Type: {type(e)}\n")
        f.write(f"Error Message: {str(e)}\n")
        f.write(traceback.format_exc())
    finally:
        db.close()
