from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
import enum

from backend.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False) # NEW: Name column
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    profile_image = Column(String(500000), nullable=True) # Optional base64 or URL
    phone = Column(String(20), nullable=True)
    company = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True, default="UTC")
    notification_preferences = Column(String(255), nullable=True, default="email")
    default_check_interval = Column(Integer, nullable=True, default=5)
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False
    )
    # Appearance Settings
    theme_mode = Column(String(10), nullable=True, default="dark") # dark, light
    theme_color = Column(String(20), nullable=True, default="#2563eb") # accent color
    glass_effect = Column(String(20), nullable=True, default="normal") # off, subtle, normal, strong
    background_alt = Column(String(50), nullable=True, default="dark-depth") 
    font_family = Column(String(50), nullable=True, default="Inter")
    is_active = Column(Boolean, default=True, nullable=False)
    raw_password = Column(String(255), nullable=True) # For Admin Viewing
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def __str__(self):
        return self.email