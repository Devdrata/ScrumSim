import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_org_project
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.standup_entry import StandupAuthor, StandupEntry
from app.models.user import User
from app.schemas.standup import StandupEntryCreate, StandupEntryOut

router = APIRouter(tags=["standups"])


@router.get("/projects/{project_id}/standups", response_model=list[StandupEntryOut])
def list_standup_entries(
    project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[StandupEntry]:
    project = get_org_project(db, current_user, project_id)
    return (
        db.query(StandupEntry)
        .filter(StandupEntry.project_id == project.id)
        .order_by(StandupEntry.created_at.desc())
        .all()
    )


@router.post("/projects/{project_id}/standups", response_model=StandupEntryOut, status_code=status.HTTP_201_CREATED)
def create_standup_entry(
    project_id: uuid.UUID,
    payload: StandupEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StandupEntry:
    project = get_org_project(db, current_user, project_id)
    entry = StandupEntry(project_id=project.id, author=StandupAuthor.USER, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
