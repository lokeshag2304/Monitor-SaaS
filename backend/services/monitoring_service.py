import httpx
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from backend.models.user import User, UserRole
from backend.models.incident import Incident
from backend.models.incident_update import IncidentUpdate
from backend.models.monitor_status_history import MonitorStatusHistory
from backend.services.email_service import send_alert_email
from backend.services.integration_service import dispatch_integration_alerts

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

async def check_website_http(url: str, timeout: int = 5):
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
        
    try:
        async with httpx.AsyncClient(verify=False, headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
            start_time = datetime.now()
            response = await client.get(url)
            end_time = datetime.now()
            
            duration_ms = (end_time - start_time).total_seconds() * 1000
            status = response.status_code
            # Status codes considered UP: 2xx, 3xx, 403 (for bot blocks), 401 (needs auth)
            is_up = (200 <= status < 400) or status == 403 or status == 401
            
            error_msg = None
            if not is_up:
                status_map = {
                    404: "Not Found (404)",
                    500: "Internal Server Error (500)",
                    502: "Bad Gateway (502)",
                    503: "Service Unavailable (503)",
                    504: "Gateway Timeout (504)"
                }
                error_msg = status_map.get(status, f"HTTP {status} Error")

            if status == 403:
                print(f"[!] {url} returned 403 (Bot Block), marking as UP. Time: {duration_ms}ms")
            else:
                print(f"[*] {url} check: {status} in {duration_ms}ms")
            
            return {
                "is_up": is_up,
                "status_code": status,
                "response_time": duration_ms,
                "error": error_msg
            }
    except httpx.ConnectTimeout:
        return {"is_up": False, "status_code": 0, "response_time": 0, "error": "Connection Timeout"}
    except httpx.ReadTimeout:
        return {"is_up": False, "status_code": 0, "response_time": 0, "error": "Read Timeout"}
    except httpx.ConnectError:
        return {"is_up": False, "status_code": 0, "response_time": 0, "error": "Connection Refused/Failed"}
    except Exception as e:
        error_msg = str(e)
        if "getaddrinfo failed" in error_msg or "Name or service not known" in error_msg:
            error_msg = "DNS Resolution Failed"
        
        print(f"[X] {url} check failed: {error_msg}")
        return {
            "is_up": False,
            "status_code": 0,
            "response_time": 0,
            "error": error_msg
        }

async def process_monitoring_check(db: Session):
    websites = db.query(Website).all()
    print(f"[*] Checking {len(websites)} websites...")
    
    for site in websites:
        if site.status == WebsiteStatus.PAUSED:
            print(f"[*] Skipping {site.url} (PAUSED)")
            continue
            
        result = await check_website_http(site.url)
        # ── 3 CONSECUTIVE FAILURES RULE (Avoid False Positives) ──
        if result["is_up"]:
            site.consecutive_failures = 0
            new_status = WebsiteStatus.UP
        else:
            site.consecutive_failures += 1
            if site.consecutive_failures >= 3:
                new_status = WebsiteStatus.DOWN
            else:
                # Soft failure: hasn't reached 3 fails yet.
                # Maintain OLD status until threshold is met or reset.
                new_status = site.status

        now = datetime.utcnow()

        # ── PART 3: Write status history on every check ──────────────────────
        status_history = MonitorStatusHistory(
            monitor_id=site.id,
            status=new_status.value,
            response_time=result["response_time"],
            checked_at=now
        )
        db.add(status_history)

        # Status page update logic removed since status_pages concept is fully rewritten as a public dashboard.

        # ── Alert + Incident Logic – only on status CHANGE ───────────────────
        if site.status != WebsiteStatus.UNKNOWN and site.status != new_status:
            print(f"[!] STATUS CHANGE: {site.url} | {site.status.value.upper()} -> {new_status.value.upper()}")
            
            owner = db.query(User).filter(User.id == site.owner_id).first()
            error_detail = result.get("error") or f"Status Code: {result.get('status_code')}"
            
            if owner:
                # Dispatch Integrations
                await dispatch_integration_alerts(db, owner.id, site.name or site.url, site.url, new_status.value, error_detail)

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
                db.flush()
                
                # Add initial update history
                db.add(IncidentUpdate(
                    incident_id=new_incident.id,
                    status=new_status.value,
                    message=f"Incident opened: {new_incident.reason}",
                    timestamp=now
                ))
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
                    
                    # Add resolution history
                    db.add(IncidentUpdate(
                        incident_id=open_incident.id,
                        status=new_status.value,
                        message=f"Incident resolved: Service is UP again.",
                        timestamp=now
                    ))

        # ── PART 5: Manage up_since for uptime duration ──────────────────────
        if new_status == WebsiteStatus.UP:
            if site.status != WebsiteStatus.UP or site.up_since is None:
                site.up_since = now
        else:
            site.up_since = None

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