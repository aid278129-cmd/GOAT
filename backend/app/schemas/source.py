from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SourceResponse(BaseModel):
    id: str
    name: str
    publisher: str
    source_type: str
    source_url: Optional[str] = None
    authority_level: str
    access_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
