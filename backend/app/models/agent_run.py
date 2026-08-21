import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentType(str, enum.Enum):
    PLANNER = "planner"
    STANDUP = "standup"
    BACKLOG = "backlog"
    RETRO = "retro"
    SRS_INTAKE = "srs_intake"


class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An agent's proposed action, awaiting human approval before it is applied.

    `proposed_output` is agent_type-specific JSON (e.g. planner -> task assignments,
    backlog -> new priority_rank ordering, standup -> summary text, retro -> discussion
    points). Nothing in proposed_output is written to core tables until approved.
    """

    __tablename__ = "agent_runs"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType, name="agent_type"), nullable=False)
    input_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    proposed_output: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus, name="agent_run_status"), default=AgentRunStatus.PENDING, nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship()
    project: Mapped["Project | None"] = relationship()
