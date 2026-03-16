from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from backend.database import Base

class WebsiteStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    ERROR = "error"
    ACTIVE = "active"
    ACTIVE_UPPER = "ACTIVE"
    UP_UPPER = "UP"
    DOWN_UPPER = "DOWN"
    PAUSED = "paused"
    PENDING = "pending"

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String(2048), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    check_interval = Column(Integer, default=5, nullable=False)
    status = Column(Enum(WebsiteStatus), default=WebsiteStatus.UNKNOWN, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Advanced Settings
    region = Column(String(50), default="Default", nullable=True)
    notifications = Column(String(255), default='["email"]', nullable=True)
    timeout = Column(Integer, default=30, nullable=True)
    keyword = Column(String(255), nullable=True)
    ssl_check = Column(Integer, default=1, nullable=True) # sqlite boolean representation
    redirect_follow = Column(Integer, default=1, nullable=True)

    owner = relationship("User", backref="websites", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Website(id={self.id}, url='{self.url}', status='{self.status}')>"