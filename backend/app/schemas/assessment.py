from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.product_dna import ProductDNACore, ClarificationRequirement
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.services.applicability.engine import ApplicabilityDecision
from backend.app.services.gap_analysis.engine import StandardComplianceEvaluation
from backend.app.services.gap_analysis.graph_builder import EvidenceGraphData
from backend.app.services.gap_analysis.evidence_extractor import StructuredEvidence
from backend.app.services.laboratory.test_roadmap import TestRoadmapItem, RecognizedLaboratory


class AssessmentCreateRequest(BaseModel):
    product_name: str
    category: str
    description: str = Field(..., min_length=5)
    authoritative_mode: bool = False
    document_ids: List[str] = Field(default_factory=list)


class AssessmentUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    mode: Optional[str] = None


class AssessmentSummaryResponse(BaseModel):
    assessment_id: str
    product_id: str
    assessment_number: str
    status: str
    mode: str
    total_requirements: int = 0
    satisfied_count: int = 0
    potentially_satisfied_count: int = 0
    missing_evidence_count: int = 0
    more_information_required_count: int = 0
    potential_gaps_count: int = 0
    not_applicable_count: int = 0
    conflicting_evidence_count: int = 0
    expert_review_count: int = 0
    recommended_actions: Dict[str, int] = Field(default_factory=dict)
    summary_verdict: str
    trust_basis: Dict[str, Any] = Field(default_factory=dict)


class AssessmentSnapshotRecord(BaseModel):
    snapshot_id: str
    assessment_id: str
    version: int
    trigger_event: str
    created_at: datetime
    knowledge_version: str
    summary_counts: Dict[str, Any]


class PassportTrustSection(BaseModel):
    verified_official_metadata: bool = True
    verified_regulatory_sources: bool = True
    full_standard_text_status: str = "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"
    synthetic_development_data_used: bool = False
    trust_level_summary: str
    dataset_name: str = "BIS-standards-dataset"
    knowledge_version: str = "v1.2.0-gazette-verified"
    knowledge_source: str = "Official Gazette QCO Registry"


class PassportSourceIndexItem(BaseModel):
    source_index_id: str
    citation_type: str  # STANDARD | REGULATION | PRODUCT_MANUAL | LAB_REPORT | CERTIFICATE
    title: str
    standard_or_gazette_number: str
    clause_or_section: Optional[str] = None
    page: Optional[int] = None
    url: Optional[str] = None
    authority: str
    verification_status: str


class CompliancePassport(BaseModel):
    passport_id: str
    assessment_id: str
    assessment_number: str
    product_name: str
    category: str
    mode: str
    generated_at: datetime
    claim_statement: str = "Evidence-Backed Regulatory Compliance Roadmap (Pre-Certification Assessment)"
    trust_basis: PassportTrustSection
    product_dna: ProductDNACore
    applicable_standards: List[ApplicabilityDecision]
    compliance_evaluations: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    testing_roadmap: List[TestRoadmapItem]
    recognized_laboratories: List[RecognizedLaboratory]
    recommended_actions: List[Dict[str, Any]]
    source_index: List[PassportSourceIndexItem]
    limitations: List[str]
    dataset_version: str = "v1.2.0-gazette-verified"
    knowledge_source: str = "BIS-standards-dataset (v1.2.0-gazette-verified)"


class AssessmentDetailResponse(BaseModel):
    assessment_id: str
    product_id: str
    assessment_number: str
    title: str
    status: str
    mode: str
    current_version: int
    knowledge_version: str = "v1.2.0-gazette-verified"
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    product_dna: ProductDNACore
    clarifications: List[ClarificationRequirement]
    applicability: List[ApplicabilityDecision]
    compliance: Optional[StandardComplianceEvaluation] = None
    evidence_items: List[StructuredEvidence] = Field(default_factory=list)
    evidence_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    testing_roadmap: List[TestRoadmapItem] = Field(default_factory=list)
    laboratories: List[RecognizedLaboratory] = Field(default_factory=list)
    evidence_graph: EvidenceGraphData
    summary: AssessmentSummaryResponse


class AssessmentChatRequest(BaseModel):
    message: str


class AssessmentChatResponse(BaseModel):
    answer: str
    assessment_id: str
    context_used: Dict[str, Any]
    citations: List[Dict[str, Any]]
    disclaimer: str
