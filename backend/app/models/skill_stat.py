import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserSkillStat(UUIDPrimaryKeyMixin, Base):
    """Demonstrated skill history for a user, built up as their assigned tasks complete.

    Distinct from the self-declared `User.skills` tags - this is earned, not claimed.
    """

    __tablename__ = "user_skill_stats"
    __table_args__ = (UniqueConstraint("user_id", "skill", name="uq_user_skill_stats_user_skill"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_story_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
