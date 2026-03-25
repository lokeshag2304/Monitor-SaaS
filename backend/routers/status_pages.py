import os
import shutil
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.status_page import StatusPage, StatusGroup, StatusGroupItem
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.incident import Incident
from backend.models.user import User, UserRole
from backend.utils.dependencies import get_current_user
from backend.schemas.status_page import StatusPageCreate, StatusPageResponse, StatusGroupCreate

router = APIRouter(prefix="/api/status-pages", tags=["Status Pages"])

@router.get("", response_model=List[StatusPageResponse])
def list_status_pages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if current_user.role == UserRole.ADMIN:
            pages = db.query(StatusPage).all()
        else:
            pages = db.query(StatusPage).filter(StatusPage.created_by == current_user.id).all()
        return pages
    except Exception as e:
        import traceback
        print("ERROR IN list_status_pages:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def create_status_page(
    page_data: StatusPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if slug exists
    if db.query(StatusPage).filter(StatusPage.slug == page_data.slug).first():
        raise HTTPException(status_code=400, detail="Slug already in use")

    new_page = StatusPage(
        name=page_data.name,
        slug=page_data.slug,
        custom_message=page_data.custom_message,
        created_by=current_user.id
    )
    db.add(new_page)
    db.flush()

    for g_data in page_data.groups:
        new_group = StatusGroup(name=g_data.name, status_page_id=new_page.id)
        db.add(new_group)
        db.flush()
        
        for item in g_data.items:
            db.add(StatusGroupItem(group_id=new_group.id, monitor_id=item.monitor_id))
            
    db.commit()
    db.refresh(new_page)
    return {"id": new_page.id, "message": "Status page created successfully"}

@router.delete("/{page_id}")
def delete_status_page(page_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if current_user.role != UserRole.ADMIN and page.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(page)
    db.commit()
    return {"message": "Deleted successfully"}

@router.post("/{page_id}/logo")
def upload_logo(
    page_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if current_user.role != UserRole.ADMIN and page.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    upload_dir = os.path.join("frontend", "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"logo_{page_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    logopath = f"/static/uploads/{filename}"
    page.logo = logopath
    db.commit()
    
    return {"logo_url": logopath}

# ── PUBLIC STATUS PAGE ENPOINT ────────────────────────────────────────────────
@router.get("/public/{slug}")
def get_public_status_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(StatusPage).filter(StatusPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
        
    overall_status = "All Systems Operational"
    groups = []
    monitors_ids = []

    for group in page.groups:
        group_items = []
        group_down = False
        
        for item in group.items:
            mon = db.query(Website).filter(Website.id == item.monitor_id).first()
            if not mon: continue
            
            monitors_ids.append(mon.id)
            
            # Use CheckResult to find if currently down based on last result
            last_check = db.query(CheckResult).filter(CheckResult.website_id == mon.id).order_by(desc(CheckResult.checked_at)).first()
            is_up = True
            if last_check:
                is_up = last_check.is_up
            else:
                # Fallback to status enum
                is_up_fallback = mon.status in [WebsiteStatus.UP, WebsiteStatus.ACTIVE]
                is_up = is_up_fallback

            # Bar history (last 30)
            history_checks = db.query(CheckResult.is_up).filter(CheckResult.website_id == mon.id).order_by(desc(CheckResult.checked_at)).limit(30).all()
            history = [h[0] for h in reversed(history_checks)]

            if not is_up:
                group_down = True
                
            group_items.append({
                "name": mon.name or mon.url,
                "status": "Operational" if is_up else "Outage",
                "up": is_up,
                "history": history
            })
            
        group_status = "Operational"
        if group_down:
            group_status = "Partial Outage"
            overall_status = "Partial Outage"
            
        groups.append({
            "name": group.name,
            "status": group_status,
            "monitors": group_items
        })
        
    # Incidents matching the monitors
    incidents = []
    if monitors_ids:
        raw_incidents = db.query(Incident).filter(Incident.monitor_id.in_(monitors_ids)).order_by(desc(Incident.started_at)).limit(10).all()
        for i in raw_incidents:
            incidents.append({
                "title": f"Issue on {i.monitor_name}",
                "status": "Resolved" if i.resolved_at else "Ongoing",
                "duration": f"{round((i.duration_seconds or i.duration or 0)/60)}m" if i.resolved_at else "Pending",
                "timestamp": i.started_at.isoformat()
            })

    return {
        "name": page.name,
        "logo": page.logo,
        "message": page.custom_message,
        "overall_status": overall_status,
        "last_updated": datetime.utcnow().isoformat(),
        "groups": groups,
        "incidents": incidents
    }
