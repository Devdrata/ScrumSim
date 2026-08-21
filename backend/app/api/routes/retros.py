import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_org_sprint
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.retro_entry import RetroEntry
from app.models.user import User
from app.schemas.retro import RetroEntryCreate, RetroEntryOut

router = APIRouter(tags=["retros"])


@router.get("/sprints/{sprint_id}/retro", response_model=list[RetroEntryOut])
def list_retro_entries(
    sprint_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RetroEntry]:
    sprint = get_org_sprint(db, current_user, sprint_id)
    return db.query(RetroEntry).filter(RetroEntry.sprint_id == sprint.id).order_by(RetroEntry.created_at).all()


@router.post("/sprints/{sprint_id}/retro", response_model=RetroEntryOut, status_code=status.HTTP_201_CREATED)
def create_retro_entry(
    sprint_id: uuid.UUID,
    payload: RetroEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetroEntry:
    sprint = get_org_sprint(db, current_user, sprint_id)
    entry = RetroEntry(sprint_id=sprint.id, created_by=current_user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
