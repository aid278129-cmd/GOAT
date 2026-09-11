from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class AmendmentSummary(BaseModel):
    amendment_number: str
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    affected_clauses: Optional[str] = None
    description: Optional[str] = None
    verification_status: str = "REQUIRES_REVIEW"


class SourceSummary(BaseModel):
    publisher: Optional[str] = None
    authority: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None


class VersionInfo(BaseModel):
    edition: Optional[str] = None
    revision: Optional[str] = None
    version: Optional[str] = None
    publication_date: Optional[date] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None


class StandardKnowledgeCard(BaseModel):
    """Consolidated knowledge card for a standard.

    Only populated from actual stored data — no manufactured summaries.
    """
    standard_number: str
    title: str
    status: str
    verification_status: str
    category: str
    scheme: str
    scope: Optional[str] = None
    source: SourceSummary = Field(default_factory=SourceSummary)
    version_information: VersionInfo = Field(default_factory=VersionInfo)
    amendments: List[AmendmentSummary] = Field(default_factory=list)
    clause_count: int = 0
    document_hash: Optional[str] = None
    ingestion_status: Optional[str] = None
    provenance_notes: Optional[str] = None
