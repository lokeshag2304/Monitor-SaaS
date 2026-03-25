from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models.incident import Incident
from backend.models.website import Website
from backend.models.user import User, UserRole
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("/")
def get_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None), # All, Ongoing, Resolved
    search: Optional[str] = Query(None)
):
    user_role = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    
    query = db.query(Incident)
    
    # Filter by user if not admin
    if user_role.upper() != "ADMIN":
        query = query.filter(Incident.user_id == current_user.id)
    
    # Filter by status
    if status:
        if status.lower() == "ongoing":
            query = query.filter(Incident.resolved_at == None)
        elif status.lower() == "resolved":
            query = query.filter(Incident.resolved_at != None)
            
    # Filter by search (monitor name)
    if search:
        query = query.filter(Incident.monitor_name.ilike(f"%{search}%"))
        
    incidents = query.order_by(desc(Incident.started_at)).all()
    
    # Calculate Stats
    total_count = len(incidents)
    ongoing_count = sum(1 for i in incidents if i.resolved_at is None)
    resolved_count = total_count - ongoing_count
    
    # Avg Duration (of resolved ones)
    resolved_incidents = [i for i in incidents if i.resolved_at is not None]
    avg_duration_secs = 0
    if resolved_incidents:
        total_duration = sum(i.duration_seconds or 0 for i in resolved_incidents)
        avg_duration_secs = total_duration / len(resolved_incidents)
        
    def format_duration(seconds):
        if not seconds: return "0s"
        if seconds < 60: return f"{int(seconds)}s"
        if seconds < 3600: return f"{int(seconds // 60)}m"
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

    results = []
    for inc in incidents:
        state = "Ongoing" if inc.resolved_at is None else "Resolved"
        duration_val = inc.duration_seconds or 0
        if inc.resolved_at is None:
            # For ongoing, calculate duration from now
            duration_val = (datetime.utcnow() - inc.started_at).total_seconds()
            
        results.append({
            "id": inc.id,
            "monitor_name": inc.monitor_name or "Unknown",
            "status_change": inc.new_status or "DOWN",
            "state": state,
            "started_at": inc.started_at.isoformat() if inc.started_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "duration": format_duration(duration_val),
            "duration_seconds": duration_val,
            "reason": inc.reason or "No details",
            "updates": [
                {
                    "status": u.status,
                    "message": u.message,
                    "timestamp": u.timestamp.isoformat()
                } for u in sorted(inc.updates, key=lambda x: x.timestamp)
            ]
        })
        
    return {
        "stats": {
            "total": total_count,
            "ongoing": ongoing_count,
            "resolved": resolved_count,
            "avg_duration": format_duration(avg_duration_secs)
        },
        "incidents": results
    }
