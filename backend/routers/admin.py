from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.user import User
from backend.models.check_result import CheckResult
from backend.utils.dependencies import get_current_admin_user
from backend.schemas.user import UserResponse
from backend.utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    users = db.query(User).all()
    res = []
    for u in users:
        res.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "is_active": u.is_active,
            "raw_password": u.raw_password, # NEW: Return plaintext password
            "created_at": u.created_at
        })
    return res

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int, 
    is_active: bool = Body(..., embed=True),
    db: Session = Depends(get_db), 
    admin_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = is_active
    db.commit()
    return {"message": f"User status updated", "is_active": user.is_active}

@router.put("/users/{user_id}/password")
def reset_user_password(
    user_id: int, 
    new_password: str = Body(..., embed=True),
    db: Session = Depends(get_db), 
    admin_user: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(new_password)
    user.raw_password = new_password # Save for Admin
    db.commit()
    return {"message": "User password updated successfully"}

@router.get("/logs", summary="Get all monitoring logs (Admin only)")
def get_all_logs(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    logs = db.query(CheckResult).order_by(desc(CheckResult.checked_at)).limit(100).all()
    return logs