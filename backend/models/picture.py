from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from core.database import Base


class PictureVisibility(Base):
    """Junction table for many-to-many relationship between pictures and framilies."""
    __tablename__ = "picture_visibility"

    id = Column(Integer, primary_key=True, index=True)
    picture_id = Column(String(36), ForeignKey("pictures.id", ondelete="CASCADE"), nullable=False)
    framily_id = Column(Integer, ForeignKey("framilies.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    picture = relationship("Picture", back_populates="visibility_records")
    framily = relationship("Framily", back_populates="picture_visibility")


class Picture(Base):
    __tablename__ = "pictures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSON, default=dict)
    # Optional caption set by the uploader (see schemas.picture.CAPTION_MAX_LENGTH
    # for the enforced length limit). Empty/unset is stored as NULL, not "",
    # so overlay code and the frontend can treat "no caption" uniformly.
    description = Column(String(300), nullable=True)
    # Optional focus rectangle, normalized to fractions (0-1) of the stored
    # image's own width/height: {"x", "y", "width", "height"}. Framily- and
    # orientation-agnostic by construction - it describes a region of the
    # original picture, not of any particular frame's output. NULL means no
    # focus area is set, and /frame/fetch falls back to a plain center crop.
    focus_area = Column(JSON, nullable=True)

    # Relationships
    uploader = relationship("User", back_populates="pictures")
    visibility_records = relationship("PictureVisibility", back_populates="picture", cascade="all, delete-orphan")

    @property
    def framilies(self):
        """Return all framilies this picture is visible to."""
        return [v.framily for v in self.visibility_records]

    @property
    def framily_ids(self):
        """Return all framily IDs this picture is visible to."""
        return [v.framily_id for v in self.visibility_records]

    @property
    def url(self) -> str:
        return f"/api/v1/pictures/{self.id}"
