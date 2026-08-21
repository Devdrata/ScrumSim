import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_admin
from app.db import get_db
from app.models.backlog_item import BacklogItem
from app.models.project import Project
from app.models.skill_stat import UserSkillStat
from app.models.team import Team
from app.models.user import User
from app.schemas.member import AssignedItemOut, MemberAdminUpdate, MemberOut, MemberSelfUpdate, SkillStatOut

router = APIRouter(prefix="/members", tags=["members"])
me_router = APIRouter(prefix="/me", tags=["members"])


def _to_member_out(db: Session, user: User) -> MemberOut:
    stats = db.query(UserSkillStat).filter(UserSkillStat.user_id == user.id).all()
    return MemberOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        skills=user.skills,
        skill_stats=[SkillStatOut.model_validate(s) for s in stats],
    )


def _get_org_member(db: Session, current_user: User, user_id: uuid.UUID) -> User:
    member = db.get(User, user_id)
    if member is None or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    return member


@router.get("", response_model=list[MemberOut])
def list_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MemberOut]:
    members = db.query(User).filter(User.org_id == current_user.org_id).order_by(User.created_at).all()
    return [_to_member_out(db, m) for m in members]


@router.patch("/me", response_model=MemberOut)
def update_my_profile(
    payload: MemberSelfUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MemberOut:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return _to_member_out(db, current_user)


@router.patch("/{user_id}", response_model=MemberOut)
def update_member(
    user_id: uuid.UUID,
    payload: MemberAdminUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MemberOut:
    member = _get_org_member(db, current_user, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return _to_member_out(db, member)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> None:
    member = _get_org_member(db, current_user, user_id)
    if member.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself")
    db.delete(member)
    db.commit()


@me_router.get("/assigned-items", response_model=list[AssignedItemOut])
def list_my_assigned_items(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AssignedItemOut]:
    rows = (
        db.query(BacklogItem, Project.name)
        .join(Project, Project.id == BacklogItem.project_id)
        .join(Team, Team.id == Project.team_id)
        .filter(BacklogItem.assignee_id == current_user.id, Team.org_id == current_user.org_id)
        .order_by(BacklogItem.updated_at.desc())
        .all()
    )
    return [
        AssignedItemOut(
            id=item.id,
            project_id=item.project_id,
            project_name=project_name,
            title=item.title,
            item_type=item.item_type,
            status=item.status,
            story_points=item.story_points,
            deadline=item.deadline,
            updated_at=item.updated_at,
        )
        for item, project_name in rows
    ]
