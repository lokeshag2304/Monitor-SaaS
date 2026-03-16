from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.database import init_db
from backend.routers import auth, websites, pagespeed, notifications, admin, monitors, reports # ADDED NEW ROUTERS
from backend.services.scheduler_service import start_scheduler
from fastapi.responses import FileResponse

app = FastAPI(
    title="MoniFy-Ping",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INCLUDE NEW ROUTERS
app.include_router(auth.router)
app.include_router(websites.router)
app.include_router(pagespeed.router)
app.include_router(notifications.router)
app.include_router(admin.router) # ADMIN ROUTER
app.include_router(monitors.router) # MONITORS ROUTER
app.include_router(reports.router, prefix="/api") # REPORTS ROUTER

# ── FRONTEND INTEGRATION ───────────────────────────────────────────────────
# Calculate base directory (abspath handles different ways of running the script)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(base_dir, "frontend")

# Mount Static Assets (/static/css, /static/js, etc.)
if os.path.exists(os.path.join(frontend_dir, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

@app.get("/monitors/{id}", tags=["Pages"])
def serve_monitor_page(id: int):
    path = os.path.join(frontend_dir, "static", "monitor.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/monitors/{id}/edit", tags=["Pages"])
def serve_edit_monitor_page(id: int):
    path = os.path.join(frontend_dir, "static", "edit_monitor.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/incidents", tags=["Pages"])
def serve_incidents_page():
    path = os.path.join(frontend_dir, "static", "incidents.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/reports", tags=["Pages"])
def serve_reports_page():
    path = os.path.join(frontend_dir, "static", "reports.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/register.html", tags=["Pages"])
def serve_register_page():
    path = os.path.join(frontend_dir, "register.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/dashboard.html", tags=["Pages"])
def serve_dashboard_html_page():
    # Serve the real dashboard from static folder
    path = os.path.join(frontend_dir, "static", "dashboard.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.get("/index.html", tags=["Pages"])
def serve_index_html_page():
    path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print(">>> Starting MoniFy-Ping...")
    init_db()
    start_scheduler()
    print("[+] Scheduler & DB Ready")
    print("=" * 60)

@app.get("/", tags=["Root"])
def root():
    # Primary entry point: Index/Login page
    path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {
        "status": "online", 
        "service": "MoniFy-Ping", 
        "version": "1.0",
        "error": "frontend/index.html not found"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "MoniFy-Ping",
        "version": "1.0.0"
    }