import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.rbac import require_admin
from app.auth.security import create_access_token, hash_password
from app.config import get_settings
from app.db import get_db
from app.models.invite import Invite, InviteStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import TokenResponse, UserOut
from app.schemas.invite import InviteAcceptRequest, InviteCreate, InviteOut, InvitePreview

router = APIRouter(prefix="/invites", tags=["invites"])
settings = get_settings()


def _accept_url(token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/accept-invite/{token}"


def _to_out(invite: Invite) -> InviteOut:
    return InviteOut(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        status=invite.status,
        accept_url=_accept_url(invite.token),
        created_at=invite.created_at,
    )


@router.post("", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def create_invite(
    payload: InviteCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> InviteOut:
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    invite = Invite(
        org_id=current_user.org_id,
        email=payload.email,
        role=payload.role,
        token=secrets.token_urlsafe(32),
        invited_by=current_user.id,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return _to_out(invite)


@router.get("", response_model=list[InviteOut])
def list_invites(current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[InviteOut]:
    invites = (
        db.query(Invite)
        .filter(Invite.org_id == current_user.org_id, Invite.status == InviteStatus.PENDING)
        .order_by(Invite.created_at.desc())
        .all()
    )
    return [_to_out(invite) for invite in invites]


@router.delete("/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(
    invite_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> None:
    invite = db.get(Invite, invite_id)
    if invite is None or invite.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    invite.status = InviteStatus.REVOKED
    db.commit()


@router.get("/{token}", response_model=InvitePreview)
def preview_invite(token: str, db: Session = Depends(get_db)) -> InvitePreview:
    invite = db.query(Invite).filter(Invite.token == token).first()
    if invite is None or invite.status != InviteStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found or no longer valid")
    org = db.get(Organization, invite.org_id)
    return InvitePreview(org_name=org.name if org else "", email=invite.email)


@router.post("/{token}/accept", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def accept_invite(token: str, payload: InviteAcceptRequest, db: Session = Depends(get_db)) -> TokenResponse:
    invite = db.query(Invite).filter(Invite.token == token).first()
    if invite is None or invite.status != InviteStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found or no longer valid")

    existing_user = db.query(User).filter(User.email == invite.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    user = User(
        org_id=invite.org_id,
        email=invite.email,
        hashed_password=hash_password(payload.password),
        role=invite.role,
    )
    db.add(user)
    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token_str = create_access_token(user_id=user.id, org_id=user.org_id)
    return TokenResponse(access_token=token_str, user=UserOut.model_validate(user))
