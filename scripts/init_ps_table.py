from backend.database import engine, Base
from backend.models import pagespeed, user, website, check_result, incident, monitor_status_history, status_page

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
