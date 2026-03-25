from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from backend.database import init_db
from backend.routers import auth, websites, pagespeed, notifications, admin, monitors, reports, incidents, user, status_pages, integrations # ADDED NEW ROUTERS
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
app.include_router(reports.router) # REPORTS ROUTER
app.include_router(incidents.router) # INCIDENTS ROUTER
app.include_router(user.router) # USER ROUTER
app.include_router(user.router_api) # USER API ROUTER
app.include_router(status_pages.router) # STATUS PAGES ROUTER
app.include_router(integrations.router) # INTEGRATIONS ROUTER

# ── FRONTEND INTEGRATION ───────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent.parent
frontend_dir = base_dir / "frontend"

# Mount Static Assets (/static/css, /static/js, etc.)
if (frontend_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")

# EXPLICIT UPLOADS MOUNT to support direct /uploads/filename structure
uploads_dir = frontend_dir / "static" / "uploads"
if not uploads_dir.exists():
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Helper to serve HTML files
def serve_html(filename: str, use_static=True):
    path = frontend_dir / "static" / filename if use_static else frontend_dir / filename
    if not path.exists() and use_static: # Try root if static fails
        path = frontend_dir / filename
    if path.exists():
        return FileResponse(str(path))
    return FileResponse(str(frontend_dir / "index.html")) # Fallback

@app.get("/monitors/{id}", tags=["Pages"])
def serve_monitor_page(id: int):
    return serve_html("monitor.html")

@app.get("/monitors/{id}/edit", tags=["Pages"])
def serve_edit_monitor_page(id: int):
    return serve_html("edit_monitor.html")

@app.get("/incidents", tags=["Pages"])
@app.get("/incidents.html", tags=["Pages"])
def serve_incidents_page():
    return serve_html("incidents.html")

@app.get("/reports", tags=["Pages"])
@app.get("/reports.html", tags=["Pages"])
def serve_reports_page():
    return serve_html("reports.html")

@app.get("/pagespeed", tags=["Pages"])
@app.get("/pagespeed.html", tags=["Pages"])
def serve_pagespeed_page():
    return serve_html("pagespeed.html")

@app.get("/register.html", tags=["Pages"])
def serve_register_page():
    return serve_html("register.html", use_static=False)

@app.get("/dashboard", tags=["Pages"])
@app.get("/dashboard.html", tags=["Pages"])
def serve_dashboard_page():
    return serve_html("dashboard.html")

@app.get("/monitoring", tags=["Pages"])
@app.get("/monitoring.html", tags=["Pages"])
def serve_monitoring_page():
    return serve_html("monitoring.html")

@app.get("/status-pages", tags=["Pages"])
@app.get("/status-pages.html", tags=["Pages"])
def serve_status_pages():
    return serve_html("status_pages.html")

@app.get("/status/{slug}", tags=["Pages"])
def serve_public_status_page(slug: str):
    return serve_html("public_status.html")

@app.get("/integrations", tags=["Pages"])
def serve_integrations_page():
    return serve_html("integrations.html")

@app.get("/settings", tags=["Pages"])
@app.get("/settings.html", tags=["Pages"])
def serve_settings_page():
    return serve_html("settings.html")

@app.get("/support", tags=["Pages"])
@app.get("/support.html", tags=["Pages"])
def serve_support_page():
    return serve_html("support.html")

@app.get("/api/integrations", tags=["API"])
def get_integrations():
    return []

@app.get("/index.html", tags=["Pages"])
def serve_index_html_page():
    return serve_html("index.html", use_static=False)

# Final Fallback: Serve any static file from frontend root
# (Like app.use(express.static("public")))
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend_root")

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print(f">>> Starting MoniFy-Ping at {base_dir}")
    print(f">>> Frontend: {frontend_dir}")
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