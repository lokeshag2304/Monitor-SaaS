import httpx
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_slack_alert(webhook_url: str, message: str, is_up: bool):
    color = "good" if is_up else "danger"
    payload = {
        "attachments": [
            {
                "color": color,
                "text": message
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=5)

async def send_discord_alert(webhook_url: str, message: str, is_up: bool):
    color = 3066993 if is_up else 15158332 # Green or Red
    payload = {
        "embeds": [
            {
                "description": message,
                "color": color
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=5)

async def send_custom_webhook(endpoint: str, method: str, headers_json: str, body_template: str, context: dict):
    # Parse headers
    headers = {}
    if headers_json:
        try:
            headers = json.loads(headers_json)
        except:
            pass
            
    # Replace variables in template
    body = body_template
    for k, v in context.items():
        body = body.replace(f"{{{{{k}}}}}", str(v))
        
    async with httpx.AsyncClient() as client:
        if method.upper() == "POST":
            # Guessing it's JSON if no content type is set
            content_kw = {}
            try:
                content_kw["json"] = json.loads(body)
            except:
                content_kw["data"] = body
            await client.post(endpoint, headers=headers, timeout=5, **content_kw)
        else:
            await client.get(endpoint, headers=headers, timeout=5)

async def create_github_issue(token: str, repo: str, title: str, body: str):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "title": title,
        "body": body,
        "labels": ["bug", "monitoring"]
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload, timeout=5)

def send_smtp_email_sync(host, port, email_addr, password, from_name, secure, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{email_addr}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        if secure:
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
            server.starttls()
            
        server.login(email_addr, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"SMTP Error: {e}")

async def send_smtp_email(config_dict, to_email: str, subject: str, body: str):
    await asyncio.to_thread(
        send_smtp_email_sync, 
        config_dict.get('smtp_host'),
        int(config_dict.get('smtp_port', 587)),
        config_dict.get('email'),
        config_dict.get('password'),
        config_dict.get('from_name', 'MoniFy Alerts'),
        config_dict.get('secure', False),
        to_email,
        subject,
        body
    )

async def dispatch_integration_alerts(db, owner_id: int, site_name: str, site_url: str, new_status: str, error_detail: str):
    from backend.models.integration import Integration
    from backend.models.user import User

    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner: return
    
    integrations = db.query(Integration).filter(Integration.user_id == owner_id, Integration.is_enabled == True).all()
    
    is_up = new_status.upper() == "UP"
    status_icon = "✅" if is_up else "🚨"
    message = f"{status_icon} Monitor Alert: **{site_name}** ({site_url}) is now **{new_status.upper()}**.\nDetails: {error_detail}"
    
    for intg in integrations:
        try:
            config = json.loads(intg.config)
            
            if intg.provider == "slack":
                await send_slack_alert(config.get("webhook_url"), message, is_up)
                
            elif intg.provider == "discord":
                await send_discord_alert(config.get("webhook_url"), message, is_up)
                
            elif intg.provider == "webhook":
                context = {
                    "site_name": site_name,
                    "site_url": site_url,
                    "status": new_status.upper(),
                    "error": error_detail,
                    "is_up": str(is_up).lower()
                }
                await send_custom_webhook(
                    config.get("endpoint_url"), 
                    config.get("method", "POST"), 
                    config.get("headers", "{}"), 
                    config.get("body_template", ""), 
                    context
                )
                
            elif intg.provider == "github":
                if not is_up and config.get("enable_issues", True):
                    title = f"Alert: {site_name} is DOWN"
                    body = f"Monitor **{site_name}** ({site_url}) went down.\n\nError: {error_detail}"
                    await create_github_issue(config.get("github_token"), config.get("repository"), title, body)
                    
            elif intg.provider == "email":
                subject = f"MoniFy Alert: {site_name} is {new_status.upper()}"
                html_body = f"<h3>{status_icon} {site_name} is {new_status.upper()}</h3><p>URL: {site_url}</p><p>Details: {error_detail}</p>"
                await send_smtp_email(config, owner.email, subject, html_body)
                
        except Exception as e:
            print(f"Error dispatching via {intg.provider}: {e}")
