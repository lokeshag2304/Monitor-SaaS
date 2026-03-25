from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class IncidentUpdate(Base):
    __tablename__ = "incident_updates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False) # e.g., DOWN, INVESTIGATING, RESOLVED
    message = Column(Text, nullable=True) # Full error or manual update
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="updates")

# Update Incident model to include relationship
# I will edit backend/models/incident.py next
