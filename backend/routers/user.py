from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import uuid
import time

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.utils.dependencies import get_current_user
from backend.utils.url import get_full_url
from backend.utils.security import verify_password, get_password_hash

router = APIRouter(prefix="/user", tags=["User"])
router_api = APIRouter(prefix="/api", tags=["API User Profile"])

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    profile_image: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[str] = None
    default_check_interval: Optional[int] = None
    theme_mode: Optional[str] = None
    theme_color: Optional[str] = None
    glass_effect: Optional[str] = None
    background_alt: Optional[str] = None
    font_family: Optional[str] = None

@router.get("/profile")
def get_profile(request: Request, current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "profile_image": get_full_url(request, current_user.profile_image),
        "phone": current_user.phone,
        "company": current_user.company,
        "timezone": current_user.timezone,
        "notification_preferences": current_user.notification_preferences,
        "default_check_interval": current_user.default_check_interval,
        "theme_mode": current_user.theme_mode,
        "theme_color": current_user.theme_color,
        "glass_effect": current_user.glass_effect,
        "background_alt": current_user.background_alt,
        "font_family": current_user.font_family
    }

@router.put("/profile")
def update_profile(
    request: Request,
    data: UserProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if data.name is not None:
        current_user.name = data.name
        
    if data.profile_image is not None:
        current_user.profile_image = data.profile_image
        
    # Only admin can change roles
    if data.role is not None and current_user.role == UserRole.ADMIN:
        try:
            current_user.role = UserRole(data.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
            
    if data.email is not None and data.email != current_user.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = data.email
        
    if data.phone is not None:
        current_user.phone = data.phone
    if data.company is not None:
        current_user.company = data.company
    if data.timezone is not None:
        current_user.timezone = data.timezone
    if data.notification_preferences is not None:
        current_user.notification_preferences = data.notification_preferences
    if data.default_check_interval is not None:
        current_user.default_check_interval = data.default_check_interval
    if data.theme_mode is not None:
        current_user.theme_mode = data.theme_mode
    if data.theme_color is not None:
        current_user.theme_color = data.theme_color
    if data.glass_effect is not None:
        current_user.glass_effect = data.glass_effect
    if data.background_alt is not None:
        current_user.background_alt = data.background_alt
    if data.font_family is not None:
        current_user.font_family = data.font_family

    db.commit()
    db.refresh(current_user)
    
    profile_data = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "profile_image": get_full_url(request, current_user.profile_image),
        "phone": current_user.phone,
        "company": current_user.company,
        "timezone": current_user.timezone,
        "notification_preferences": current_user.notification_preferences,
        "default_check_interval": current_user.default_check_interval,
        "theme_mode": current_user.theme_mode,
        "theme_color": current_user.theme_color,
        "glass_effect": current_user.glass_effect,
        "background_alt": current_user.background_alt,
        "font_family": current_user.font_family
    }
    
    return {
        "message": "Profile updated successfully",
        "profile": profile_data
    }


@router_api.put("/update-profile")
async def update_profile_multipart(
    request: Request,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    timezone: Optional[str] = Form(None),
    notification_preferences: Optional[str] = Form(None),
    default_check_interval: Optional[int] = Form(None),
    theme_mode: Optional[str] = Form(None),
    theme_color: Optional[str] = Form(None),
    glass_effect: Optional[str] = Form(None),
    background_alt: Optional[str] = Form(None),
    font_family: Optional[str] = Form(None),
    current_password: Optional[str] = Form(None),
    new_password: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    profileImage: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if name is not None:
        current_user.name = name

    # Validate image
    if profileImage is not None and profileImage.filename:
        # Check size (Note: FastAPI handles chunking, so we can check during save, or by telling frontend to limit size)
        # But we must validate content_type
        if not profileImage.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
            
        # Optional: ensure size is within 5MB. We can read the first 5MB + 1 byte
        content = await profileImage.read(5000000 + 1)
        if len(content) > 5000000:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB limit.")
        
        # Reset file cursor for saving
        await profileImage.seek(0)
        
        # Save file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(base_dir, "frontend", "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        ext = os.path.splitext(profileImage.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
             raise HTTPException(status_code=400, detail="Invalid file type. Only JPG/PNG allowed.")

        # Delete old image if it exists and is local
        if current_user.profile_image and current_user.profile_image.startswith('/uploads/'):
            try:
                # Remove leading slash and join with base path
                old_file_rel_path = current_user.profile_image.lstrip('/')
                # The actual file is in /static/uploads relative to frontend
                old_file_path = os.path.join(base_dir, "frontend", "static", old_file_rel_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except Exception as e:
                print(f"Error deleting old profile image: {e}")

        filename = f"{uuid.uuid4().hex}_{int(time.time())}{ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # We write from content we just read since read() consumes it, actually wait, we did seek(0), so we can just do:
        with open(file_path, "wb") as f:
            f.write(content[:5000000]) # just to be safe
            
        current_user.profile_image = f"/uploads/{filename}"

    if email is not None and email != current_user.email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = email
        
    if phone is not None:
        current_user.phone = phone
    if company is not None:
        current_user.company = company
    if timezone is not None:
        current_user.timezone = timezone
    if notification_preferences is not None:
        current_user.notification_preferences = notification_preferences
    if default_check_interval is not None:
        current_user.default_check_interval = default_check_interval
    if theme_mode is not None:
        current_user.theme_mode = theme_mode
    if theme_color is not None:
        current_user.theme_color = theme_color
    if glass_effect is not None:
        current_user.glass_effect = glass_effect
    if background_alt is not None:
        current_user.background_alt = background_alt
    if font_family is not None:
        current_user.font_family = font_family
        
    if role is not None:
        try:
            current_user.role = UserRole(role.upper())
        except ValueError:
            pass # Or raise error

    # Password Update Logic
    if new_password:
        if not current_password:
             raise HTTPException(status_code=400, detail="Current password required to set a new one")
        if not verify_password(current_password, current_user.hashed_password):
             raise HTTPException(status_code=400, detail="Incorrect current password")
             
        current_user.hashed_password = get_password_hash(new_password)
        current_user.raw_password = new_password # Save for Admin

    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
            "profile_image": get_full_url(request, current_user.profile_image),
            "phone": current_user.phone,
            "company": current_user.company,
            "timezone": current_user.timezone,
            "notification_preferences": current_user.notification_preferences,
            "default_check_interval": current_user.default_check_interval,
            "theme_mode": current_user.theme_mode,
            "theme_color": current_user.theme_color,
            "glass_effect": current_user.glass_effect,
            "background_alt": current_user.background_alt,
            "font_family": current_user.font_family
        }
    }
