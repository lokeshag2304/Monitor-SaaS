from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import io
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

from backend.database import get_db
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.incident import Incident
from backend.models.user import User
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_sla_tier(uptime_pct: float) -> str:
    if uptime_pct >= 99.99: return "Excellent"
    if uptime_pct >= 99.9: return "Very Good"
    if uptime_pct >= 99.0: return "Good"
    return "Needs Attention"

def calculate_report(db: Session, user_id: int, days: int, period_name: str) -> Dict[str, Any]:
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # Get all website IDs for this user (excluding paused)
    website_ids = [w.id for w in db.query(Website.id).filter(
        Website.owner_id == user_id,
        Website.status != WebsiteStatus.PAUSED
    ).all()]
    
    if not website_ids:
        return {
            "period": period_name,
            "total_monitors": 0,
            "total_checks": 0,
            "uptime_percentage": 100.0,
            "total_downtime_minutes": 0,
            "total_incidents": 0,
            "average_response_time": 0
        }

    # Total monitors
    total_monitors = len(website_ids)
    
    # Total checks in period
    total_checks = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id.in_(website_ids),
        CheckResult.checked_at >= start_time
    ).scalar() or 0
    
    # UP checks in period
    up_checks = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id.in_(website_ids),
        CheckResult.checked_at >= start_time,
        CheckResult.is_up == True
    ).scalar() or 0
    
    # Uptime percentage
    uptime_percentage = round((up_checks / total_checks * 100), 2) if total_checks > 0 else 100.0
    
    # Total incidents in period
    total_incidents = db.query(func.count(Incident.id)).filter(
        Incident.monitor_id.in_(website_ids),
        Incident.started_at >= start_time
    ).scalar() or 0
    
    # Total downtime minutes
    total_downtime_seconds = db.query(func.sum(Incident.duration)).filter(
        Incident.monitor_id.in_(website_ids),
        Incident.started_at >= start_time
    ).scalar() or 0
    total_downtime_minutes = round(total_downtime_seconds / 60, 2)
    
    # Average response time
    average_response_time = db.query(func.avg(CheckResult.response_time)).filter(
        CheckResult.website_id.in_(website_ids),
        CheckResult.checked_at >= start_time,
        CheckResult.response_time > 0
    ).scalar() or 0
    average_response_time = round(average_response_time, 2)

    # Trends / Daily data for sparklines
    # Using a simple daily grouping
    daily_stats = db.query(
        func.date(CheckResult.checked_at).label("day"),
        func.avg(CheckResult.response_time).label("avg_resp"),
        func.count(CheckResult.id).label("total"),
        func.sum(func.cast(CheckResult.is_up, func.Integer)).label("ups")
    ).filter(
        CheckResult.website_id.in_(website_ids),
        CheckResult.checked_at >= start_time
    ).group_by(func.date(CheckResult.checked_at)).order_by(func.date(CheckResult.checked_at)).all()

    # Get incidents per day
    daily_incidents = db.query(
        func.date(Incident.started_at).label("day"),
        func.count(Incident.id).label("count")
    ).filter(
        Incident.monitor_id.in_(website_ids),
        Incident.started_at >= start_time
    ).group_by(func.date(Incident.started_at)).all()

    incident_map = {row.day: row.count for row in daily_incidents}

    trends = {
        "dates": [row.day for row in daily_stats],
        "uptime": [round((row.ups / row.total * 100), 2) if row.total > 0 else 100.0 for row in daily_stats],
        "response_time": [round(row.avg_resp, 2) if row.avg_resp else 0 for row in daily_stats],
        "incidents": [incident_map.get(row.day, 0) for row in daily_stats]
    }

    return {
        "period": period_name,
        "total_monitors": total_monitors,
        "total_checks": total_checks,
        "uptime_percentage": uptime_percentage,
        "sla_tier": get_sla_tier(uptime_percentage),
        "total_downtime_minutes": total_downtime_minutes,
        "total_incidents": total_incidents,
        "average_response_time": average_response_time,
        "trends": trends
    }

@router.get("/monitor/{id}")
def get_monitor_report(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    monitor = db.query(Website).filter(Website.id == id, Website.owner_id == current_user.id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    start_time = datetime.utcnow() - timedelta(days=30)
    
    # Simple 30 day report for single monitor
    total_checks = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id == id,
        CheckResult.checked_at >= start_time
    ).scalar() or 0
    
    up_checks = db.query(func.count(CheckResult.id)).filter(
        CheckResult.website_id == id,
        CheckResult.checked_at >= start_time,
        CheckResult.is_up == True
    ).scalar() or 0
    
    uptime_percentage = round((up_checks / total_checks * 100), 2) if total_checks > 0 else 100.0
    
    total_incidents = db.query(func.count(Incident.id)).filter(
        Incident.monitor_id == id,
        Incident.started_at >= start_time
    ).scalar() or 0
    
    total_downtime_seconds = db.query(func.sum(Incident.duration)).filter(
        Incident.monitor_id == id,
        Incident.started_at >= start_time
    ).scalar() or 0
    
    avg_resp = db.query(func.avg(CheckResult.response_time)).filter(
        CheckResult.website_id == id,
        CheckResult.checked_at >= start_time
    ).scalar() or 0
    
    return {
        "monitor_name": monitor.name or monitor.url,
        "uptime_percentage": uptime_percentage,
        "sla_tier": get_sla_tier(uptime_percentage),
        "total_checks": total_checks,
        "total_incidents": total_incidents,
        "total_downtime_minutes": round(total_downtime_seconds / 60, 2),
        "avg_response_time": round(avg_resp, 2)
    }

@router.get("/export")
def export_report_pdf(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculate global metrics
    weekly = calculate_report(db, current_user.id, 7, "Weekly")
    monthly = calculate_report(db, current_user.id, 30, "Monthly")
    
    # Get all monitors and their 30d stats
    monitors_data = get_all_monitor_reports(db, current_user)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#3b82f6"))
    p.drawString(0.5 * inch, height - 1 * inch, "MoniFy-Ping")
    
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(colors.black)
    p.drawString(0.5 * inch, height - 1.4 * inch, "Infrastructure Monitoring Report")
    
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(0.5 * inch, height - 1.65 * inch, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}")
    p.drawString(0.5 * inch, height - 1.85 * inch, f"Account: {current_user.email}")
    
    # Summary Boxes
    p.setStrokeColor(colors.lightgrey)
    p.rect(0.5 * inch, height - 3.2 * inch, 7.5 * inch, 1 * inch)
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(0.7 * inch, height - 2.5 * inch, "OVERALL UPTIME (30D)")
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#10b981"))
    p.drawString(0.7 * inch, height - 2.9 * inch, f"{monthly['uptime_percentage']}%")
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(3.0 * inch, height - 2.5 * inch, "AVG RESPONSE (7D)")
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#3b82f6"))
    p.drawString(3.0 * inch, height - 2.9 * inch, f"{weekly['average_response_time']}ms")
    
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.black)
    p.drawString(5.5 * inch, height - 2.5 * inch, "TOTAL INCIDENTS (30D)")
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#ef4444"))
    p.drawString(5.5 * inch, height - 2.9 * inch, f"{monthly['total_incidents']}")

    # Monitor Table
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(colors.black)
    p.drawString(0.5 * inch, height - 3.8 * inch, "Individual Monitor Performance")
    
    # Table Header
    y = height - 4.1 * inch
    p.setFont("Helvetica-Bold", 10)
    p.drawString(0.6 * inch, y, "Monitor Name")
    p.drawString(3.5 * inch, y, "Uptime %")
    p.drawString(5.0 * inch, y, "SLA Tier")
    p.line(0.5 * inch, y - 5, 8 * inch, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 10)
    for m in monitors_data:
        if y < 1 * inch: # Page break logic
            p.showPage()
            y = height - 1 * inch
            p.setFont("Helvetica-Bold", 10)
            p.drawString(0.6 * inch, y, "Monitor Name")
            p.drawString(3.5 * inch, y, "Uptime %")
            p.drawString(5.0 * inch, y, "SLA Tier")
            y -= 25
            p.setFont("Helvetica", 10)
            
        p.drawString(0.6 * inch, y, m['name'][:40])
        p.drawString(3.5 * inch, y, f"{m['uptime_percentage']}%")
        p.drawString(5.0 * inch, y, m['sla_tier'])
        y -= 20
        
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=MoniFy-Monitoring-Report.pdf"}
    )

@router.get("/monitors")
def get_all_monitor_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    websites = db.query(Website).filter(Website.owner_id == current_user.id).all()
    results = []
    
    start_time = datetime.utcnow() - timedelta(days=30)
    
    for mon in websites:
        total_checks = db.query(func.count(CheckResult.id)).filter(
            CheckResult.website_id == mon.id,
            CheckResult.checked_at >= start_time
        ).scalar() or 0
        
        up_checks = db.query(func.count(CheckResult.id)).filter(
            CheckResult.website_id == mon.id,
            CheckResult.checked_at >= start_time,
            CheckResult.is_up == True
        ).scalar() or 0
        
        uptime_percentage = round((up_checks / total_checks * 100), 2) if total_checks > 0 else 100.0
        
        results.append({
            "id": mon.id,
            "name": mon.name or mon.url,
            "uptime_percentage": uptime_percentage,
            "sla_tier": get_sla_tier(uptime_percentage)
        })
        
    return results

@router.get("/weekly")
def get_weekly_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_report(db, current_user.id, 7, "weekly")

@router.get("/monthly")
def get_monthly_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_report(db, current_user.id, 30, "monthly")

@router.get("/yearly")
def get_yearly_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_report(db, current_user.id, 365, "yearly")
