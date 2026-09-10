"""Pydantic v2 Input and Output Schemas for Controlled LangChain Tools (M24.3).

All tools are bounded, typed, and schema-validated.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# 1. Search BIS Standards Schemas
# ------------------------------------------------------------------------------
class SearchStandardsInput(BaseModel):
    """Input parameters for searching verified Indian Standards."""
    query: str = Field(..., min_length=1, max_length=200, description="Product category or standard number keywords")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of candidate standards to return")


class StandardCandidateItem(BaseModel):
    standard_number: str
    title: str
    ministry: Optional[str] = None
    qco_order: Optional[str] = None
    verified: bool = True


class SearchStandardsOutput(BaseModel):
    candidates: List[StandardCandidateItem] = Field(default_factory=list)
    total_found: int
    query: str


# ------------------------------------------------------------------------------
# 2. Search BIS Clauses Schemas
# ------------------------------------------------------------------------------
class SearchClausesInput(BaseModel):
    """Input parameters for searching clauses within a verified standard."""
    standard_number: str = Field(..., min_length=3, max_length=50, description="Target standard number (e.g. IS 302-2-201:2008)")
    query: str = Field(default="", max_length=200, description="Clause title, requirement keywords, or clause number")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of clauses to return")


class ClauseCandidateItem(BaseModel):
    standard_number: str
    clause_number: str
    clause_title: str
    requirement_text: str
    verified: bool = True


class SearchClausesOutput(BaseModel):
    standard_number: str
    clauses: List[ClauseCandidateItem] = Field(default_factory=list)
    total_returned: int


# ------------------------------------------------------------------------------
# 3. Get Verified Evidence Schemas
# ------------------------------------------------------------------------------
class GetVerifiedEvidenceInput(BaseModel):
    """Input parameters for querying permitted, verified evidence records."""
    evidence_ids: List[str] = Field(..., min_length=1, max_length=20, description="List of evidence identifiers to inspect")
    standard_number: Optional[str] = Field(None, max_length=50, description="Optional target standard context")


class VerifiedEvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: str
    source_name: str
    verification_status: str
    is_verified: bool
    summary: str


class GetVerifiedEvidenceOutput(BaseModel):
    records: List[VerifiedEvidenceItem] = Field(default_factory=list)
    total_verified: int
    unverified_suppressed: List[str] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# 4. Normalize Unit Schemas
# ------------------------------------------------------------------------------
class NormalizeUnitInput(BaseModel):
    """Input parameters for physical engineering unit conversion."""
    value: float = Field(..., description="Numeric value to convert")
    from_unit: str = Field(..., min_length=1, max_length=20, description="Original unit of measurement")
    to_unit: str = Field(..., min_length=1, max_length=20, description="Target normalized unit")


class NormalizeUnitOutput(BaseModel):
    original_value: float
    from_unit: str
    converted_value: float
    to_unit: str
    conversion_applied: bool


# ------------------------------------------------------------------------------
# 5. Get Product Facts Schemas
# ------------------------------------------------------------------------------
class GetProductFactsInput(BaseModel):
    """Input parameters for reading permitted Product DNA facts."""
    product_name: Optional[str] = Field(None, max_length=100, description="Product identifier or name")
    category: Optional[str] = Field(None, max_length=100, description="Product category")


class ProductFactItem(BaseModel):
    field_name: str
    value: Any
    unit: Optional[str] = None
    provenance: str
    verification_state: str


class GetProductFactsOutput(BaseModel):
    product_name: str
    category: str
    facts: List[ProductFactItem] = Field(default_factory=list)
    total_facts: int
