from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.integration_credential import IntegrationProvider


class GitHubCredentialIn(BaseModel):
    token: str = Field(min_length=1)
    repo: str = Field(min_length=1, pattern=r"^[^/\s]+/[^/\s]+$", description="owner/repo")


class JiraCredentialIn(BaseModel):
    site_url: str = Field(min_length=1)
    email: EmailStr
    api_token: str = Field(min_length=1)
    project_key: str = Field(min_length=1)


class SlackCredentialIn(BaseModel):
    bot_token: str = Field(min_length=1)
    channel: str = Field(min_length=1)


class IntegrationStatusOut(BaseModel):
    provider: IntegrationProvider
    connected: bool
    configured_at: datetime | None = None
    detail: dict | None = None
