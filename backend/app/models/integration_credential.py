import enum
import uuid

from sqlalchemy import Enum, ForeignKey, LargeBinary, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationProvider(str, enum.Enum):
    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"


class IntegrationCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores provider credentials encrypted at rest.

    `encrypted_payload` is a Fernet-encrypted JSON blob (see app/integrations/crypto.py)
    whose shape depends on `provider` (e.g. github -> {token, repo}, jira -> {site_url,
    email, api_token, project_key}, slack -> {bot_token, channel}).
    """

    __tablename__ = "integration_credentials"
    __table_args__ = (UniqueConstraint("org_id", "provider", name="uq_org_provider"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider, name="integration_provider"), nullable=False
    )
    encrypted_payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    organization: Mapped["Organization"] = relationship()
