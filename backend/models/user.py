from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
import enum

from backend.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    ADMIN_UPPER = "ADMIN"
    USER_UPPER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False) # NEW: Name column
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def __str__(self):
        return self.email