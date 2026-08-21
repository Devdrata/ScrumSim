from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_admin
from app.db import get_db
from app.integrations import github_client, jira_client, slack_client
from app.integrations.crypto import encrypt_payload
from app.integrations.exceptions import IntegrationError
from app.models.integration_credential import IntegrationCredential, IntegrationProvider
from app.models.user import User
from app.schemas.integration import GitHubCredentialIn, IntegrationStatusOut, JiraCredentialIn, SlackCredentialIn

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _parse_provider(provider: str) -> IntegrationProvider:
    try:
        return IntegrationProvider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown integration provider") from exc


def _test_credential(provider: IntegrationProvider, payload: dict) -> dict:
    if provider == IntegrationProvider.GITHUB:
        creds = GitHubCredentialIn(**payload)
        return github_client.test_connection(creds.token, creds.repo)
    if provider == IntegrationProvider.JIRA:
        creds = JiraCredentialIn(**payload)
        return jira_client.test_connection(creds.site_url, creds.email, creds.api_token)
    creds = SlackCredentialIn(**payload)
    return slack_client.test_connection(creds.bot_token)


def _validate_and_test(provider: IntegrationProvider, payload: dict) -> dict:
    try:
        return _test_credential(provider, payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[IntegrationStatusOut])
def list_integrations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[IntegrationStatusOut]:
    rows = {
        row.provider: row
        for row in db.query(IntegrationCredential).filter(IntegrationCredential.org_id == current_user.org_id)
    }
    return [
        IntegrationStatusOut(
            provider=provider,
            connected=provider in rows,
            configured_at=rows[provider].created_at if provider in rows else None,
        )
        for provider in IntegrationProvider
    ]


@router.post("/{provider}/test", response_model=IntegrationStatusOut)
def test_integration(
    provider: str, payload: dict, current_user: User = Depends(get_current_user)
) -> IntegrationStatusOut:
    provider_enum = _parse_provider(provider)
    detail = _validate_and_test(provider_enum, payload)
    return IntegrationStatusOut(provider=provider_enum, connected=True, detail=detail)


@router.post("/{provider}", response_model=IntegrationStatusOut, status_code=status.HTTP_201_CREATED)
def save_integration(
    provider: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IntegrationStatusOut:
    provider_enum = _parse_provider(provider)
    detail = _validate_and_test(provider_enum, payload)

    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.org_id == current_user.org_id,
            IntegrationCredential.provider == provider_enum,
        )
        .first()
    )
    encrypted = encrypt_payload(payload)
    if existing:
        existing.encrypted_payload = encrypted
        row = existing
    else:
        row = IntegrationCredential(org_id=current_user.org_id, provider=provider_enum, encrypted_payload=encrypted)
        db.add(row)
    db.commit()
    db.refresh(row)
    return IntegrationStatusOut(provider=provider_enum, connected=True, configured_at=row.created_at, detail=detail)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(
    provider: str, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> None:
    provider_enum = _parse_provider(provider)
    db.query(IntegrationCredential).filter(
        IntegrationCredential.org_id == current_user.org_id,
        IntegrationCredential.provider == provider_enum,
    ).delete()
    db.commit()
