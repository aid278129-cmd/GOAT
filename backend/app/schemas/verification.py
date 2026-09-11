from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VerificationRecordResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    verification_status: str
    verified_by: str
    verification_method: str
    source_authority: Optional[str] = None
    document_hash: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
