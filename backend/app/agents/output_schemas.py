from pydantic import BaseModel, Field


class RecommendedItem(BaseModel):
    backlog_item_id: str
    rationale: str
    assignee_user_id: str | None = None


class SprintPlanDraft(BaseModel):
    summary: str
    recommended_items: list[RecommendedItem] = Field(default_factory=list)


class StandupDraft(BaseModel):
    summary: str
    blockers: list[str] = Field(default_factory=list)


class BacklogPriorityDraft(BaseModel):
    ordered_item_ids: list[str]
    rationale: str


class RetroDraft(BaseModel):
    went_well: list[str] = Field(default_factory=list)
    went_wrong: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class SRSItemDraft(BaseModel):
    level: int
    title: str
    description: str = ""
    story_points: int | None = None
    required_skills: list[str] = Field(default_factory=list)
    acceptance_criteria: str = ""


class SRSIngestDraft(BaseModel):
    summary: str
    items: list[SRSItemDraft] = Field(default_factory=list)
