import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_org_project
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.backlog_item import BacklogItem, BacklogItemStatus
from app.models.project import Project
from app.models.skill_stat import UserSkillStat
from app.models.user import User
from app.schemas.backlog import BacklogItemCreate, BacklogItemOut, BacklogItemUpdate, BacklogTreeNode

router = APIRouter(tags=["backlog"])


def _get_org_backlog_item(db: Session, current_user: User, item_id: uuid.UUID) -> BacklogItem:
    item = db.get(BacklogItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")
    get_org_project(db, current_user, item.project_id)
    return item


def _record_skill_completion(db: Session, item: BacklogItem) -> None:
    if item.assignee_id is None:
        return
    for skill in item.required_skills:
        stat = (
            db.query(UserSkillStat)
            .filter(UserSkillStat.user_id == item.assignee_id, UserSkillStat.skill == skill)
            .first()
        )
        if stat is None:
            stat = UserSkillStat(user_id=item.assignee_id, skill=skill, completed_task_count=0, completed_story_points=0)
            db.add(stat)
        stat.completed_task_count += 1
        stat.completed_story_points += item.story_points or 0


def _build_tree(items: list[BacklogItem]) -> list[BacklogTreeNode]:
    nodes = {item.id: BacklogTreeNode(**BacklogItemOut.model_validate(item).model_dump()) for item in items}
    roots: list[BacklogTreeNode] = []
    for item in items:
        node = nodes[item.id]
        if item.parent_id is not None and item.parent_id in nodes:
            nodes[item.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


@router.get("/projects/{project_id}/backlog", response_model=list[BacklogItemOut])
def list_backlog_items(
    project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BacklogItem]:
    project: Project = get_org_project(db, current_user, project_id)
    return (
        db.query(BacklogItem)
        .filter(BacklogItem.project_id == project.id)
        .order_by(BacklogItem.priority_rank.asc().nullslast(), BacklogItem.created_at)
        .all()
    )


@router.get("/projects/{project_id}/backlog/tree", response_model=list[BacklogTreeNode])
def get_backlog_tree(
    project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BacklogTreeNode]:
    project: Project = get_org_project(db, current_user, project_id)
    items = (
        db.query(BacklogItem)
        .filter(BacklogItem.project_id == project.id)
        .order_by(BacklogItem.priority_rank.asc().nullslast(), BacklogItem.created_at)
        .all()
    )
    return _build_tree(items)


@router.post("/projects/{project_id}/backlog", response_model=BacklogItemOut, status_code=status.HTTP_201_CREATED)
def create_backlog_item(
    project_id: uuid.UUID,
    payload: BacklogItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BacklogItem:
    project = get_org_project(db, current_user, project_id)

    data = payload.model_dump()
    parent_id = data.get("parent_id")
    if parent_id is not None:
        parent = db.get(BacklogItem, parent_id)
        if parent is None or parent.project_id != project.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent item not in this project")

    assignee_id = data.get("assignee_id")
    if assignee_id is not None:
        assignee = db.get(User, assignee_id)
        if assignee is None or assignee.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee is not an org member")

    item = BacklogItem(project_id=project.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/backlog/{item_id}", response_model=BacklogItemOut)
def update_backlog_item(
    item_id: uuid.UUID,
    payload: BacklogItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BacklogItem:
    item = _get_org_backlog_item(db, current_user, item_id)
    updates = payload.model_dump(exclude_unset=True)

    if "parent_id" in updates and updates["parent_id"] is not None:
        parent = db.get(BacklogItem, updates["parent_id"])
        if parent is None or parent.project_id != item.project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent item not in this project")

    if "assignee_id" in updates and updates["assignee_id"] is not None:
        assignee = db.get(User, updates["assignee_id"])
        if assignee is None or assignee.org_id != current_user.org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee is not an org member")

    was_done = item.status == BacklogItemStatus.DONE
    for field, value in updates.items():
        setattr(item, field, value)

    if not was_done and item.status == BacklogItemStatus.DONE:
        _record_skill_completion(db, item)

    db.commit()
    db.refresh(item)
    return item
