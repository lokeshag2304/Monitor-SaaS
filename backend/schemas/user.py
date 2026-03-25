from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    name: str # NEW
    email: EmailStr
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'user']:
            raise ValueError('Role must be either "admin" or "user"')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    profile_image: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[str] = None
    default_check_interval: Optional[int] = None
    is_active: bool = True
    
    class Config:
        orm_mode = True
        
    @validator('role', pre=True)
    def convert_enum_to_str(cls, v):
        if hasattr(v, 'value'):
            return v.value
        return v