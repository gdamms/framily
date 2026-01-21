from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class Framily(Base):
    __tablename__ = "framilies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    frame_token = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    settings = relationship("FramilySettings", back_populates="framily", uselist=False, cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="framily", cascade="all, delete-orphan")
    pictures = relationship("Picture", back_populates="framily", cascade="all, delete-orphan")


class FramilySettings(Base):
    __tablename__ = "framily_settings"

    id = Column(Integer, primary_key=True, index=True)
    framily_id = Column(Integer, ForeignKey("framilies.id", ondelete="CASCADE"), unique=True, nullable=False)
    picture_duration = Column(Integer, default=10)  # Seconds per picture
    shuffle_mode = Column(String(20), default="random")  # random, sequential
    transition_effect = Column(String(20), default="fade")  # fade, slide, etc.
    overlays = Column(JSON, default=list)  # List of overlay configurations

    # Relationships
    framily = relationship("Framily", back_populates="settings")
