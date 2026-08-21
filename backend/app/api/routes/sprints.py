import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_org_project, get_org_sprint
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.sprint import Sprint
from app.models.user import User
from app.schemas.sprint import SprintCreate, SprintOut, SprintUpdate

router = APIRouter(tags=["sprints"])


@router.get("/projects/{project_id}/sprints", response_model=list[SprintOut])
def list_sprints(
    project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Sprint]:
    project = get_org_project(db, current_user, project_id)
    return db.query(Sprint).filter(Sprint.project_id == project.id).order_by(Sprint.created_at).all()


@router.post("/projects/{project_id}/sprints", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
def create_sprint(
    project_id: uuid.UUID,
    payload: SprintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Sprint:
    project = get_org_project(db, current_user, project_id)
    sprint = Sprint(project_id=project.id, **payload.model_dump())
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.patch("/sprints/{sprint_id}", response_model=SprintOut)
def update_sprint(
    sprint_id: uuid.UUID,
    payload: SprintUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Sprint:
    sprint = get_org_sprint(db, current_user, sprint_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    return sprint
