import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RetroCategory(str, enum.Enum):
    WENT_WELL = "went_well"
    WENT_WRONG = "went_wrong"
    ACTION_ITEM = "action_item"


class RetroEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retro_entries"

    sprint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[RetroCategory] = mapped_column(Enum(RetroCategory, name="retro_category"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    sprint: Mapped["Sprint"] = relationship()
