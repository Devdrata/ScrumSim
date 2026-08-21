import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.sprint import SprintStatus


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    capacity_points: int | None = None


class SprintUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: SprintStatus | None = None
    capacity_points: int | None = None


class SprintOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    start_date: date | None
    end_date: date | None
    status: SprintStatus
    capacity_points: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
