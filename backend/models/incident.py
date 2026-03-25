from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    monitor_name = Column(String(255), nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    duration = Column(Float, nullable=True) # Keeping old column for compat
    reason = Column(String(500), nullable=True)

    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<Incident(monitor={self.monitor_id}, new_status={self.new_status}, started={self.started_at})>"

