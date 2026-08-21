import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.agent_run import AgentRunStatus, AgentType


class PlannerRunRequest(BaseModel):
    project_id: uuid.UUID
    sprint_id: uuid.UUID


class StandupRunRequest(BaseModel):
    project_id: uuid.UUID


class BacklogRunRequest(BaseModel):
    project_id: uuid.UUID


class RetroRunRequest(BaseModel):
    sprint_id: uuid.UUID


class AgentRunOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: uuid.UUID | None
    agent_type: AgentType
    input_context: dict
    proposed_output: dict
    status: AgentRunStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
