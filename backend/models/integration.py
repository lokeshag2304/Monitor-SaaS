from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from backend.database import Base

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False) # e.g. 'email', 'slack', 'discord', 'webhook', 'github'
    config = Column(Text, nullable=False) # JSON encoded dictionary of configuration params
    is_enabled = Column(Boolean, default=True)
