from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class StatusPage(Base):
    __tablename__ = "status_pages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    logo = Column(String(1024), nullable=True) # path or url
    custom_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    groups = relationship("StatusGroup", back_populates="status_page", cascade="all, delete-orphan", passive_deletes=True)

class StatusGroup(Base):
    __tablename__ = "status_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    status_page_id = Column(Integer, ForeignKey("status_pages.id", ondelete="CASCADE"), nullable=False)

    status_page = relationship("StatusPage", back_populates="groups")
    items = relationship("StatusGroupItem", back_populates="group", cascade="all, delete-orphan", passive_deletes=True)

class StatusGroupItem(Base):
    __tablename__ = "status_group_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("status_groups.id", ondelete="CASCADE"), nullable=False)
    monitor_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)

    group = relationship("StatusGroup", back_populates="items")
