import uuid

from sqlalchemy.orm import Session

from app.integrations.crypto import decrypt_payload
from app.models.integration_credential import IntegrationCredential, IntegrationProvider


def get_org_credential(db: Session, org_id: uuid.UUID, provider: IntegrationProvider) -> dict | None:
    row = (
        db.query(IntegrationCredential)
        .filter(IntegrationCredential.org_id == org_id, IntegrationCredential.provider == provider)
        .first()
    )
    if row is None:
        return None
    return decrypt_payload(row.encrypted_payload)
