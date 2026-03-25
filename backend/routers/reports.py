from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, Integer, cast
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import io
import csv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

from backend.database import get_db
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.incident import Incident
from backend.models.user import User, UserRole
from backend.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def get_summary_stats(db: Session, monitor_ids: List[int], start: datetime, end: datetime):
    total = db.query(CheckResult).filter(CheckResult.website_id.in_(monitor_ids), CheckResult.checked_at >= start, CheckResult.checked_at < end).count()
    ups = db.query(CheckResult).filter(CheckResult.website_id.in_(monitor_ids), CheckResult.checked_at >= start, CheckResult.checked_at < end, CheckResult.is_up == True).count()
    uptime = round((ups / total * 100) if total > 0 else 100.0, 2)
    
    avg_resp = db.query(func.avg(CheckResult.response_time)).filter(CheckResult.website_id.in_(monitor_ids), CheckResult.checked_at >= start, CheckResult.checked_at < end, CheckResult.response_time > 0).scalar() or 0
    
    downtime = db.query(func.sum(Incident.duration)).filter(Incident.monitor_id.in_(monitor_ids), Incident.started_at >= start, Incident.started_at < end).scalar() or 0
    
    return {
        "uptime": uptime,
        "avg_resp": round(float(avg_resp), 2),
        "total_checks": total,
        "downtime": round(float(downtime) / 60.0, 2) # in minutes
    }

@router.get("/dynamic")
def get_dynamic_report(ids: Optional[str] = Query(None), days: int = 7, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    start_p1 = now - timedelta(days=days)
    start_p2 = now - timedelta(days=2*days)
    
    if ids:
        monitor_ids = [int(i) for i in ids.split(",")]
    else:
        # Admins can see all if no IDs provided, but usually users want their own
        if current_user.role == UserRole.ADMIN:
            monitor_ids = [m.id for m in db.query(Website.id).all()]
        else:
            monitor_ids = [m.id for m in db.query(Website.id).filter(Website.owner_id == current_user.id).all()]

    if not monitor_ids:
        raise HTTPException(status_code=400, detail="No monitors found for report")

    curr_stats = get_summary_stats(db, monitor_ids, start_p1, now)
    prev_stats = get_summary_stats(db, monitor_ids, start_p2, start_p1)
    
    # Global Trends
    daily_stats = db.query(
        func.date(CheckResult.checked_at).label("day"),
        func.avg(CheckResult.response_time).label("avg_resp"),
        func.count(CheckResult.id).label("total"),
        func.sum(cast(CheckResult.is_up, Integer)).label("ups")
    ).filter(CheckResult.website_id.in_(monitor_ids), CheckResult.checked_at >= start_p1).group_by(func.date(CheckResult.checked_at)).order_by(func.date(CheckResult.checked_at)).all()

    trends = {
        "dates": [str(d.day) for d in daily_stats],
        "uptime": [round((d.ups / d.total * 100) if d.total > 0 else 100.0, 2) for d in daily_stats],
        "response_time": [round(float(d.avg_resp or 0), 2) for d in daily_stats]
    }

    # Individual Monitor Performance
    perf = []
    for mid in monitor_ids:
        site = db.query(Website).filter(Website.id == mid).first()
        if not site: continue
        
        m_s = db.query(
            func.count(CheckResult.id).label("total"),
            func.sum(cast(CheckResult.is_up, Integer)).label("ups"),
            func.avg(CheckResult.response_time).label("avg_resp")
        ).filter(CheckResult.website_id == mid, CheckResult.checked_at >= start_p1).first()
        
        m_inc = db.query(Incident).filter(Incident.monitor_id == mid, Incident.started_at >= start_p1).count()
        
        # Trend (last 12 points for sparkline)
        m_trend = db.query(CheckResult.response_time).filter(CheckResult.website_id == mid).order_by(desc(CheckResult.checked_at)).limit(12).all()
        trend_vals = [r[0] for r in reversed(m_trend)]
        
        perf.append({
            "id": mid,
            "name": site.name or site.url,
            "status": str(site.status.value) if hasattr(site.status, 'value') else str(site.status),
            "uptime_percentage": round((m_s.ups / m_s.total * 100) if m_s.total and m_s.total > 0 else 100.0, 2),
            "avg_response_time": round(float(m_s.avg_resp or 0), 2),
            "checks": m_s.total or 0,
            "incidents": m_inc,
            "trend": trend_vals
        })

    # Latest Incidents
    incidents = db.query(Incident).filter(Incident.monitor_id.in_(monitor_ids), Incident.started_at >= start_p1).order_by(desc(Incident.started_at)).limit(10).all()

    return {
        "uptime_percentage": curr_stats["uptime"],
        "average_response_time": curr_stats["avg_resp"],
        "total_checks": curr_stats["total_checks"],
        "total_downtime_minutes": curr_stats["downtime"],
        "diffs": {
            "uptime": round(curr_stats["uptime"] - prev_stats["uptime"], 2),
            "response": round(curr_stats["avg_resp"] - prev_stats["avg_resp"], 2),
            "checks": curr_stats["total_checks"] - prev_stats["total_checks"],
            "downtime": round(curr_stats["downtime"] - prev_stats["downtime"], 2)
        },
        "trends": trends,
        "monitors_performance": perf,
        "latest_incidents": [{
            "monitor_name": i.monitor_name or "Unknown",
            "started_at": i.started_at.isoformat(),
            "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
            "duration_seconds": i.duration_seconds or i.duration or 0
        } for i in incidents]
    }

@router.get("/export/csv")
def export_report_csv(days: int = 7, ids: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = get_dynamic_report(ids, days, db, current_user)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["MoniFy-Ping - Monitoring Report"])
    writer.writerow(["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    writer.writerow(["Summary Stats"])
    writer.writerow(["Overall Uptime %", data["uptime_percentage"]])
    writer.writerow(["Total Checks", data["total_checks"]])
    writer.writerow(["Avg Response Time (ms)", data["average_response_time"]])
    writer.writerow(["Total Downtime (min)", data["total_downtime_minutes"]])
    writer.writerow([])
    writer.writerow(["Monitor Performance"])
    writer.writerow(["Name", "Uptime %", "Avg Response (ms)", "Checks", "Incidents"])
    for m in data["monitors_performance"]:
        writer.writerow([m["name"], m["uptime_percentage"], m["avg_response_time"], m["checks"], m["incidents"]])
    
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return response

@router.get("/export")
def export_report_pdf(ids: Optional[str] = Query(None), days: int = 7, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = get_dynamic_report(ids, days, db, current_user)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#3b82f6"))
    p.drawString(0.5 * inch, height - 1 * inch, "MoniFy-Ping")
    
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(colors.black)
    p.drawString(0.5 * inch, height - 1.4 * inch, "Infrastructure Monitoring Report")
    
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(0.5 * inch, height - 1.65 * inch, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}")
    
    # Summary Table
    p.setStrokeColor(colors.lightgrey)
    p.rect(0.5 * inch, height - 3 * inch, 7.5 * inch, 1 * inch)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(0.7 * inch, height - 2.3 * inch, "OVERALL UPTIME")
    p.drawString(3.0 * inch, height - 2.3 * inch, "AVG RESPONSE")
    p.drawString(5.5 * inch, height - 2.3 * inch, "TOTAL CHECKS")
    
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.HexColor("#22c55e"))
    p.drawString(0.7 * inch, height - 2.7 * inch, f"{data['uptime_percentage']}%")
    p.setFillColor(colors.HexColor("#3b82f6"))
    p.drawString(3.0 * inch, height - 2.7 * inch, f"{data['average_response_time']}ms")
    p.setFillColor(colors.black)
    p.drawString(5.5 * inch, height - 2.7 * inch, f"{data['total_checks']}")
    
    # Performance
    p.setFont("Helvetica-Bold", 14)
    p.drawString(0.5 * inch, height - 3.5 * inch, "Monitor Performance")
    
    y = height - 3.8 * inch
    p.setFont("Helvetica-Bold", 10)
    p.drawString(0.6 * inch, y, "Monitor Name")
    p.drawString(3.5 * inch, y, "Uptime %")
    p.drawString(5.0 * inch, y, "Avg Resp")
    p.line(0.5 * inch, y - 5, 8 * inch, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 10)
    for m in data["monitors_performance"]:
        if y < 1 * inch:
            p.showPage()
            y = height - 1 * inch
        p.drawString(0.6 * inch, y, str(m["name"])[:40])
        p.drawString(3.5 * inch, y, f"{m['uptime_percentage']}%")
        p.drawString(5.0 * inch, y, f"{m['avg_response_time']}ms")
        y -= 20
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=MoniFy-Report.pdf"})

@router.get("/monitors")
def get_report_monitors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        monitors = db.query(Website).all()
    else:
        monitors = db.query(Website).filter(Website.owner_id == current_user.id).all()
    return [{"id": m.id, "name": m.name or m.url, "url": m.url} for m in monitors]

@router.get("/monitor/{monitor_id}")
def get_individual_monitor_report(
    monitor_id: int, 
    range: str = Query("weekly"), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    monitor = db.query(Website).filter(Website.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
        
    if current_user.role != UserRole.ADMIN and monitor.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    days_map = {'daily': 1, 'weekly': 7, 'monthly': 30, 'yearly': 365}
    days = days_map.get(range, 7)
    since = datetime.utcnow() - timedelta(days=days)

    stat = db.query(
        func.count(CheckResult.id).label('total'),
        func.sum(cast(CheckResult.is_up, Integer)).label('ups'),
        func.avg(CheckResult.response_time).label('avg_resp')
    ).filter(
        CheckResult.website_id == monitor_id,
        CheckResult.checked_at >= since
    ).first()

    total_checks = stat.total or 0
    ups = stat.ups or 0
    avg_resp = stat.avg_resp or 0

    uptime_percentage = round((ups / total_checks * 100), 2) if total_checks > 0 else 100.0

    incidents = db.query(Incident).filter(
        Incident.monitor_id == monitor_id,
        Incident.started_at >= since
    ).all()
    
    total_incidents = len(incidents)
    
    downtime_sec = sum((inc.duration_seconds or inc.duration or 0) for inc in incidents)
    total_downtime_minutes = round(downtime_sec / 60.0, 2)

    sla_tier = "Needs Attention"
    if uptime_percentage >= 99.99:
        sla_tier = "Excellent"
    elif uptime_percentage >= 99.9:
        sla_tier = "Very Good"
    elif uptime_percentage >= 99.0:
        sla_tier = "Good"

    return {
        "monitor_name": monitor.name or monitor.url,
        "uptime_percentage": uptime_percentage,
        "sla_tier": sla_tier,
        "avg_response_time": round(float(avg_resp), 2),
        "total_incidents": total_incidents,
        "total_downtime_minutes": total_downtime_minutes,
        "total_checks": total_checks
    }
