import uuid
from datetime import date

from pydantic import BaseModel


class BurndownPoint(BaseModel):
    date: date
    remaining_points: int


class SprintBurndown(BaseModel):
    sprint_id: uuid.UUID
    sprint_name: str
    status: str
    total_items: int
    completed_items: int
    completion_rate: float | None
    capacity_points: int | None
    total_points: int
    completed_points: int
    burndown_series: list[BurndownPoint] = []


class BottleneckItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    days_in_status: float
    sprint_id: uuid.UUID | None


class ProjectAnalytics(BaseModel):
    active_sprint: SprintBurndown | None
    bottlenecks: list[BottleneckItem]
    velocity: float | None
