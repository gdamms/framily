from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from core.database import Base


class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    framily_id = Column(Integer, ForeignKey("framilies.id", ondelete="CASCADE"), nullable=False)
    role = Column(Integer, default=0, nullable=False)  # 0=invited, 1=member, 2=admin
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Unique constraint: one membership per user per framily
    __table_args__ = (
        UniqueConstraint('user_id', 'framily_id', name='unique_user_framily'),
    )
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    framily = relationship("Framily", back_populates="memberships")
