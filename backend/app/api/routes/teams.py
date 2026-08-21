import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.members import _to_member_out
from app.auth.dependencies import get_current_user
from app.auth.rbac import require_admin
from app.db import get_db
from app.models.project import Project
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.member import MemberOut
from app.schemas.organization import ProjectCreate, ProjectOut, TeamCreate, TeamMemberAdd, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


def _get_org_team(db: Session, current_user: User, team_id: uuid.UUID) -> Team:
    team = db.get(Team, team_id)
    if team is None or team.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Team]:
    return db.query(Team).filter(Team.org_id == current_user.org_id).order_by(Team.created_at).all()


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> Team:
    team = Team(org_id=current_user.org_id, name=payload.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}/projects", response_model=list[ProjectOut])
def list_projects(
    team_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Project]:
    team = _get_org_team(db, current_user, team_id)
    return db.query(Project).filter(Project.team_id == team.id).order_by(Project.created_at).all()


@router.post("/{team_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    team_id: uuid.UUID,
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    team = _get_org_team(db, current_user, team_id)
    project = Project(team_id=team.id, name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{team_id}/members", response_model=list[MemberOut])
def list_team_members(
    team_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MemberOut]:
    team = _get_org_team(db, current_user, team_id)
    users = (
        db.query(User)
        .join(TeamMember, TeamMember.user_id == User.id)
        .filter(TeamMember.team_id == team.id)
        .order_by(TeamMember.joined_at)
        .all()
    )
    return [_to_member_out(db, u) for u in users]


@router.post("/{team_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_team_member(
    team_id: uuid.UUID,
    payload: TeamMemberAdd,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MemberOut:
    team = _get_org_team(db, current_user, team_id)
    member = db.get(User, payload.user_id)
    if member is None or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    existing = db.get(TeamMember, {"team_id": team.id, "user_id": member.id})
    if existing is None:
        db.add(TeamMember(team_id=team.id, user_id=member.id))
        db.commit()
    return _to_member_out(db, member)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    team = _get_org_team(db, current_user, team_id)
    membership = db.get(TeamMember, {"team_id": team.id, "user_id": user_id})
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    db.delete(membership)
    db.commit()
