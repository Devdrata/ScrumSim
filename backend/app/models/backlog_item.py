import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BacklogItemStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_SPRINT = "in_sprint"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class BacklogItemType(str, enum.Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    SUBTASK = "subtask"


class BacklogItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "backlog_items"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("backlog_items.id", ondelete="SET NULL"), nullable=True
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[BacklogItemStatus] = mapped_column(
        Enum(BacklogItemStatus, name="backlog_item_status"), default=BacklogItemStatus.BACKLOG, nullable=False
    )
    item_type: Mapped[BacklogItemType] = mapped_column(
        Enum(BacklogItemType, name="backlog_item_type"), default=BacklogItemType.TASK, nullable=False
    )
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="backlog_items")
    sprint: Mapped["Sprint | None"] = relationship(back_populates="backlog_items")
    parent: Mapped["BacklogItem | None"] = relationship(remote_side="BacklogItem.id", back_populates="children")
    children: Mapped[list["BacklogItem"]] = relationship(back_populates="parent")
    assignee: Mapped["User | None"] = relationship()
