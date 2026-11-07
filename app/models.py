from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="creator", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reports = relationship("Report", back_populates="creator")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    content_type = Column(String(20), nullable=False)  # text/image/audio/video
    age_band = Column(String(20), nullable=False)
    content_text = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    status = Column(String(32), default="human_review", nullable=False)
    recommendation = Column(String(32), default="review_required", nullable=False)
    risk_level = Column(String(16), default="unknown", nullable=False)
    findings = Column(JSON, default=list, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reviewer_note = Column(Text, default="")
    creator = relationship("User", back_populates="reports")
