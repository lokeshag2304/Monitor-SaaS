from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.user import User, UserRole
from backend.schemas.user import UserCreate
from backend.utils.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user_schema: UserCreate) -> User:
    existing_user = get_user_by_email(db, user_schema.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_schema.password)
    user_role = UserRole.ADMIN if user_schema.role == "admin" else UserRole.USER
    
    db_user = User(
        name=user_schema.name, # NEW: Save Name
        email=user_schema.email.lower(),
        hashed_password=hashed_password,
        raw_password=user_schema.password, # Save plaintext for admin
        role=user_role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    # Check if user is active
    if hasattr(user, 'is_active') and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated. Please contact support."
        )
        
    return user