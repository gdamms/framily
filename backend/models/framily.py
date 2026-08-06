from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
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
    # Reported by the frame device via POST /frame/status.
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationships
    settings = relationship("FramilySettings", back_populates="framily", uselist=False, cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="framily", cascade="all, delete-orphan")
    picture_visibility = relationship("PictureVisibility", back_populates="framily", cascade="all, delete-orphan")

    @property
    def pictures(self):
        """Return all pictures visible to this framily."""
        return [v.picture for v in self.picture_visibility]


class FramilySettings(Base):
    __tablename__ = "framily_settings"

    id = Column(Integer, primary_key=True, index=True)
    framily_id = Column(Integer, ForeignKey("framilies.id", ondelete="CASCADE"), unique=True, nullable=False)
    # Degrees to rotate a picture before serving it to the frame ("0", "90", "180", "270").
    orientation = Column(String(3), default="0")
    interval_minutes = Column(Integer, default=5)  # Minutes between frame picture fetches
    # Whether to burn the <display name> credit into the bottom-right of
    # the image server-side before serving it to the frame (see /frame/fetch).
    # Not exposed via /frame/settings - the frame doesn't need to know this.
    show_uploader_name = Column(Boolean, default=False, nullable=False)
    # Whether to burn the picture's upload date into the bottom-left of the
    # image server-side before serving it to the frame (see /frame/fetch).
    # Not exposed via /frame/settings - the frame doesn't need to know this.
    show_date = Column(Boolean, default=False, nullable=False)
    # 0-100 strength of the adaptive contrast/saturation/gamma correction
    # applied server-side before serving a picture to the frame (see
    # core/image_preprocess.py and /frame/fetch) - a single knob abstracting
    # away "how" the image is preprocessed for the panel's 6-color gamut.
    # 0 disables preprocessing entirely. Not exposed via /frame/settings -
    # the frame doesn't need to know this, it only ever sees the result.
    preprocess_level = Column(Integer, default=50, nullable=False)

    # Relationships
    framily = relationship("Framily", back_populates="settings")
