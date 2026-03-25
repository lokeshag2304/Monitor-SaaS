import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.integration import Integration
from backend.utils.dependencies import get_current_user
from backend.schemas.integration import IntegrationCreate, IntegrationResponse
from backend.services.integration_service import (
    send_slack_alert,
    send_discord_alert,
    send_smtp_email,
    send_custom_webhook,
    create_github_issue
)

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])

@router.get("", response_model=List[IntegrationResponse])
def get_user_integrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Integration).filter(Integration.user_id == current_user.id).all()
    # parse json to dict before return for the schema
    resp_list = []
    for raw in items:
        # Pydantic expects dict for `config`
        conf_dict = {}
        try:
            conf_dict = json.loads(raw.config)
        except: pass
        
        resp_list.append({
            "id": raw.id,
            "provider": raw.provider,
            "config": conf_dict,
            "is_enabled": raw.is_enabled
        })
    return resp_list

@router.post("")
def save_integration(data: IntegrationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if provider exists
    existing = db.query(Integration).filter(Integration.user_id == current_user.id, Integration.provider == data.provider).first()
    
    encoded_config = json.dumps(data.config)
    
    if existing:
        existing.config = encoded_config
        existing.is_enabled = data.is_enabled
        db.commit()
        return {"id": existing.id, "message": "Updated successfully"}
    else:
        new_int = Integration(
            user_id=current_user.id,
            provider=data.provider,
            config=encoded_config,
            is_enabled=data.is_enabled
        )
        db.add(new_int)
        db.commit()
        db.refresh(new_int)
        return {"id": new_int.id, "message": "Saved successfully"}

@router.post("/{provider}/test")
async def test_integration(provider: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Find active integration
    integration = db.query(Integration).filter(Integration.user_id == current_user.id, Integration.provider == provider).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration profile not configured.")
        
    config = json.loads(integration.config)
    
    try:
        if provider == "slack":
            await send_slack_alert(config.get("webhook_url"), "Test message from MoniFy", True)
        elif provider == "discord":
            await send_discord_alert(config.get("webhook_url"), "Test message from MoniFy", True)
        elif provider == "email":
            await send_smtp_email(config, current_user.email, "MoniFy Integration Test", "<p>Test email alert successful.</p>")
        elif provider == "webhook":
            await send_custom_webhook(
                config.get("endpoint_url"),
                config.get("method"),
                config.get("headers"),
                config.get("body_template"),
                {"site_name": "Test Monitor", "site_url": "http://test", "status": "UP", "error": "None"}
            )
        elif provider == "github":
            repo = config.get("repository")
            if not repo or "/" not in repo:
                raise HTTPException(status_code=400, detail="Invalid repository format 'owner/repo'")
            await create_github_issue(config.get("github_token"), repo, "MoniFy Test Alert", "This is a test issue from integration.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"message": "Test triggered successfully."}
