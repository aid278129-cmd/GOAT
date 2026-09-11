from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RequirementSchema(BaseModel):
    id: Optional[str] = None
    clause_id: Optional[str] = None
    code: str
    requirement_type: str = "PERFORMANCE"
    description: str
    measurable_condition: Optional[str] = None
    evidence_type: Optional[str] = None
    test_method_reference: Optional[str] = None
    interpretation_status: str = "CONFIDENT"
    verification_status: str = "REQUIRES_REVIEW"

    model_config = ConfigDict(from_attributes=True)


class ClauseBase(BaseModel):
    clause_number: str = Field(..., description="Clause number e.g. 4.2.1")
    title: str
    section: Optional[str] = None
    text_content: str
    page_number: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    parent_clause_id: Optional[str] = None
    segmentation_status: str = "CONFIDENT"
    verification_status: str = "REQUIRES_REVIEW"
    version: str = "1.0"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ClauseCreate(ClauseBase):
    standard_id: str


class ClauseResponse(ClauseBase):
    id: str
    standard_id: str
    requirements: List[RequirementSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ClauseTreeNode(ClauseBase):
    id: str
    standard_id: str
    subclauses: List["ClauseTreeNode"] = Field(default_factory=list)
    requirements: List[RequirementSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ClauseSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Semantic or keyword query")
    standard_number: Optional[str] = None
    verified_only: bool = True
    include_unverified: bool = False  # Developer inspection mode
    top_k: int = Field(default=5, ge=1, le=50)
    category: Optional[str] = None


class ClauseSearchResult(BaseModel):
    clause_id: str
    standard_id: str
    standard_number: str
    standard_title: str
    clause_number: str
    clause_title: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    text_content: str
    similarity_score: float
    lexical_score: Optional[float] = None
    dense_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: Optional[float] = None
    retrieval_mode: str = "HYBRID"
    match_factors: Dict[str, Any] = Field(default_factory=dict)
    parent_clause: Optional[Dict[str, Any]] = None
    verification_status: str
    source_authority: Optional[str] = None  # M1.5: expose trust signal
    requirements: List[RequirementSchema] = Field(default_factory=list)
    citation: Dict[str, Any] = Field(default_factory=dict)
