import httpx
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.user import User, UserRole
from backend.models.incident import Incident
from backend.models.monitor_status_history import MonitorStatusHistory
from backend.models.status_page import StatusPage
from backend.services.email_service import send_alert_email

# FULL CHROME HEADERS (The Human Mask)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

async def check_website_http(url: str, timeout: int = 15):
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
        
    try:
        async with httpx.AsyncClient(verify=False, headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
            start_time = datetime.now()
            response = await client.get(url)
            end_time = datetime.now()
            
            duration_ms = (end_time - start_time).total_seconds() * 1000
            status = response.status_code
            is_up = (200 <= status < 400) or (status == 403) or (status == 401) or (status == 503)
            
            if status == 403:
                print(f"[!] {url} returned 403 (Bot Block), marking as UP.")
            
            return {
                "is_up": is_up,
                "status_code": status,
                "response_time": duration_ms,
                "error": None
            }
    except Exception as e:
        return {
            "is_up": False,
            "status_code": 0,
            "response_time": 0,
            "error": str(e)
        }

async def process_monitoring_check(db: Session):
    websites = db.query(Website).all()
    print(f"[*] Checking {len(websites)} websites...")
    
    for site in websites:
        result = await check_website_http(site.url)
        
        new_status = WebsiteStatus.UP if result["is_up"] else WebsiteStatus.DOWN
        now = datetime.utcnow()

        # ── PART 3: Write status history on every check ──────────────────────
        status_history = MonitorStatusHistory(
            monitor_id=site.id,
            status=new_status.value,
            response_time=result["response_time"],
            checked_at=now
        )
        db.add(status_history)

        # ── PART 4: Upsert status_pages record ───────────────────────────────
        sp = db.query(StatusPage).filter(StatusPage.monitor_id == site.id).first()
        # Compute uptime % from last 100 history entries
        history_count = db.query(CheckResult).filter(CheckResult.website_id == site.id).count()
        up_count = db.query(CheckResult).filter(
            CheckResult.website_id == site.id, CheckResult.is_up == True
        ).count()
        uptime_pct = round((up_count / history_count * 100), 2) if history_count > 0 else 100.0
        if sp:
            sp.current_status = new_status.value
            sp.last_checked = now
            sp.uptime_percentage = uptime_pct
        else:
            db.add(StatusPage(
                monitor_id=site.id,
                current_status=new_status.value,
                last_checked=now,
                uptime_percentage=uptime_pct
            ))

        # ── Alert + Incident Logic – only on status CHANGE ───────────────────
        if site.status != WebsiteStatus.UNKNOWN and site.status != new_status:
            print(f"[!] STATUS CHANGE: {site.url} | {site.status.value.upper()} -> {new_status.value.upper()}")
            
            owner = db.query(User).filter(User.id == site.owner_id).first()
            if owner:
                recipients = [owner.email]
                if owner.role == UserRole.USER:
                    admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
                    for admin in admins:
                        if admin.email not in recipients:
                            recipients.append(admin.email)
                
                error_detail = result.get("error") or f"Status Code: {result.get('status_code')}"
                
                for email in recipients:
                    print(f"[>] Triggering email alert for: {email}")
                    try:
                        send_alert_email(email, site.url, new_status.value.upper(), error_detail)
                    except Exception as e:
                        print(f"[x] Error sending email to {email}: {e}")
            else:
                print(f"[!] Alert aborted: Owner ID {site.owner_id} not found.")

            # ── PART 1: Enriched Incident tracking ───────────────────────────
            if new_status == WebsiteStatus.DOWN:
                new_incident = Incident(
                    monitor_id=site.id,
                    user_id=site.owner_id,
                    monitor_name=site.name or site.url,
                    previous_status=site.status.value,
                    new_status=new_status.value,
                    started_at=now,
                    reason=result.get("error") or f"Status Code: {result.get('status_code')}"
                )
                db.add(new_incident)
            elif new_status == WebsiteStatus.UP:
                open_incident = db.query(Incident).filter(
                    Incident.monitor_id == site.id,
                    Incident.resolved_at == None
                ).order_by(Incident.started_at.desc()).first()
                if open_incident:
                    open_incident.resolved_at = now
                    open_incident.new_status = new_status.value
                    secs = (now - open_incident.started_at).total_seconds()
                    open_incident.duration = secs
                    open_incident.duration_seconds = secs

        site.status = new_status
        site.last_checked = now
        
        log_entry = CheckResult(
            website_id=site.id,
            status_code=result["status_code"],
            response_time=result["response_time"],
            is_up=result["is_up"],
            error_message=result["error"],
            checked_at=now
        )
        db.add(log_entry)
        
    db.commit()