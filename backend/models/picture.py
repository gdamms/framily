from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from core.database import Base


class Picture(Base):
    __tablename__ = "pictures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    framily_id = Column(Integer, ForeignKey("framilies.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    url = Column(String(500), nullable=False)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSON, default=dict)  # width, height, format, file_size

    # Relationships
    framily = relationship("Framily", back_populates="pictures")
    uploader = relationship("User", back_populates="pictures")
