"""User pattern model for the intelligence layer."""
import uuid
from datetime import datetime

from sqlalchemy import UUID, Float, Column, DateTime, String, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserPattern(Base):
    """User pattern model representing the user_patterns table."""

    __tablename__ = "user_patterns"

    id = Column(UUID, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # 'peak_hours', 'category_preference', 'completion_rate', 'estimation_accuracy'
    pattern_data = Column(PGJSONB, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()"))

    # Relationships
    user = relationship("User", back_populates="user_patterns")

    def __repr__(self) -> str:
        return f"<UserPattern(id={self.id}, user_id={self.user_id}, type='{self.pattern_type}')>"