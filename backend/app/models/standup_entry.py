import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StandupAuthor(str, enum.Enum):
    AGENT = "agent"
    USER = "user"


class StandupEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "standup_entries"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    author: Mapped[StandupAuthor] = mapped_column(Enum(StandupAuthor, name="standup_author"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship()
    sprint: Mapped["Sprint | None"] = relationship()
