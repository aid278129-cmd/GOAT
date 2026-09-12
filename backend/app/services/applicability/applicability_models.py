"""Layer 5: Applicability Engine — Data Models & Result States.

Implements the SIH Presentation Layer 5 architecture:
PRODUCT DNA
  ↓
APPLICABILITY FEATURES
  ↓
RULE MATCHING
  ↓
STANDARD CANDIDATES
  ↓
QCO / SCOPE VALIDATION
  ↓
APPLICABILITY DECISION
  ↓
EXPLANATION + PROVENANCE
  ↓
LAYER 6 CLAUSE RAG

Supported Result States:
- APPLICABLE
- POTENTIALLY_APPLICABLE
- MORE_INFORMATION_REQUIRED
- NOT_APPLICABLE
- COVERAGE_GAP
- CONFLICTING_RULES
- EXPERT_REVIEW_REQUIRED

Critical Invariants:
- NO VERIFIED SCOPE/RULE → NO AUTHORITATIVE APPLICABILITY CLAIM
- MISSING REQUIRED FACT → ASK
- UNKNOWN → UNKNOWN / MORE_INFORMATION_REQUIRED
- COVERAGE GAP ≠ NOT_APPLICABLE
- STANDARD EXISTS ≠ AUTOMATICALLY APPLICABLE / MANDATORY
- LLM AUTHORITY OVER FINAL APPLICABILITY = 0%
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ApplicabilityState(str, Enum):
    """The 7 canonical applicability states from SIH PPT."""
    APPLICABLE = "APPLICABLE"
    POTENTIALLY_APPLICABLE = "POTENTIALLY_APPLICABLE"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    COVERAGE_GAP = "COVERAGE_GAP"
    CONFLICTING_RULES = "CONFLICTING_RULES"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"


class ScopeStatus(str, Enum):
    """Scope determination state based on verified Layer 4 standard scope."""
    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    SCOPE_UNCERTAIN = "SCOPE_UNCERTAIN"


class QCOStatus(str, Enum):
    """QCO / Regulatory mandate determination state."""
    MANDATORY_QCO = "MANDATORY_QCO"
    VOLUNTARY = "VOLUNTARY"
    NOT_GOVERNED_BY_QCO = "NOT_GOVERNED_BY_QCO"
    QCO_UNCERTAIN = "QCO_UNCERTAIN"


class StandardStatus(str, Enum):
    """Lifecycle and gazette publication status of an Indian Standard."""
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    REVISION_PENDING = "REVISION_PENDING"
    CATALOG_ONLY = "CATALOG_ONLY"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    UNKNOWN = "UNKNOWN"


class ProductConditionStatus(str, Enum):
    """Status of conditional requirement evaluation for the product."""
    CONDITIONS_SATISFIED = "CONDITIONS_SATISFIED"
    CONDITIONS_UNMET = "CONDITIONS_UNMET"
    CONDITIONS_PENDING_INFO = "CONDITIONS_PENDING_INFO"
    NOT_CONDITIONAL = "NOT_CONDITIONAL"


class NormativeDependencyStatus(str, Enum):
    """Status of normative / allied standard references."""
    PRIMARY_ONLY = "PRIMARY_ONLY"
    HAS_NORMATIVE_DEPENDENCIES = "HAS_NORMATIVE_DEPENDENCIES"
    DEPENDENCY_UNMET = "DEPENDENCY_UNMET"
    NORMATIVE_REFERENCE_CANDIDATE = "NORMATIVE_REFERENCE_CANDIDATE"


class EvidenceAvailabilityStatus(str, Enum):
    """Status of clause-level textual evidence in verified repository."""
    FULL_TEXT_VERIFIED = "FULL_TEXT_VERIFIED"
    METADATA_ONLY = "METADATA_ONLY"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    COVERAGE_GAP = "COVERAGE_GAP"


class NormativeRelationType(str, Enum):
    """Relationship category between Indian Standards."""
    PRIMARY_STANDARD = "PRIMARY_STANDARD"
    NORMATIVE_REFERENCE = "NORMATIVE_REFERENCE"
    RELATED_STANDARD = "RELATED_STANDARD"
    SUPERSEDES = "SUPERSEDES"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    AMENDMENT_OF = "AMENDMENT_OF"
    APPLICABILITY_DEPENDENCY = "APPLICABILITY_DEPENDENCY"


class NormativeStandardReference(BaseModel):
    """Deterministic reference to an allied or normative standard."""
    standard_number: str
    title: Optional[str] = None
    relationship_type: NormativeRelationType = NormativeRelationType.NORMATIVE_REFERENCE
    clause_reference: Optional[str] = None
    description: Optional[str] = None
    is_mandatory_dependency: bool = False
    dependency_condition: Optional[str] = None
    standard_status: StandardStatus = StandardStatus.ACTIVE


class TypedCondition(BaseModel):
    """Declarative typed condition for deterministic conditional applicability."""
    condition_id: str
    description: str
    field: str
    operator: str  # "equals", "contains", "in", "greater_than", "less_than", "exists", "between", "not_equals"
    expected_value: Any
    unit: Optional[str] = None
    is_mandatory_discriminator: bool = False


class ConditionalRequirementEvaluation(BaseModel):
    """Result of evaluating a typed condition against Product DNA."""
    condition_id: str
    condition_description: str
    attribute_evaluated: str
    actual_value: Any = None
    expected_value: Any = None
    status: str = "SATISFIED"  # "SATISFIED", "UNMET", "MISSING_ATTRIBUTE", "UNKNOWN"
    explanation: str = ""


class StandardRevisionInfo(BaseModel):
    """Authoritative standard revision and gazette status metadata."""
    standard_number: str
    standard_title: str
    revision_edition: str
    status: StandardStatus = StandardStatus.ACTIVE
    publication_year: Optional[int] = None
    effective_date: Optional[str] = None
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    amendments: List[str] = Field(default_factory=list)
    gazette_order_ref: Optional[str] = None
    provenance: str = "Bureau of Indian Standards"


class ApplicabilityAction(str, Enum):
    """Next operational action triggered by applicability state."""
    CONTINUE_TO_REQUIREMENTS = "CONTINUE_TO_REQUIREMENTS"
    ASK_FOR_INFORMATION = "ASK_FOR_INFORMATION"
    REVIEW_COVERAGE_GAP = "REVIEW_COVERAGE_GAP"
    EXPERT_REVIEW = "EXPERT_REVIEW"


class SupportingFact(BaseModel):
    """A product fact that contributed to the applicability determination."""
    field_name: str
    value: Any
    unit: Optional[str] = None
    source: str = "PRODUCT_DNA"
    provenance: Optional[str] = None
    confidence: float = 1.0


class RuleSourceReference(BaseModel):
    """Reference to an authoritative regulatory knowledge source."""
    source_type: str = "BIS_OFFICIAL"
    publisher: str = "Bureau of Indian Standards"
    url: Optional[str] = None


class DeclarativeRule(BaseModel):
    """Declarative regulatory rule for matching Indian Standards."""
    rule_id: str
    name: str
    description: str
    priority: int = 10
    verification_status: str = "VERIFIED"  # VERIFIED | REQUIRES_EXPERT_REVIEW | DEVELOPMENT_ONLY
    conditions: Dict[str, Any]
    result: Dict[str, Any]
    sources: List[RuleSourceReference] = Field(default_factory=list)


class DeterministicDecisionTrace(BaseModel):
    """Full deterministic step-by-step decision trace."""
    product_facts: List[str] = Field(default_factory=list)
    matched_rule: Optional[str] = None
    standard: str
    scope_check: ScopeStatus = ScopeStatus.IN_SCOPE
    scope_reason: str
    qco_check: QCOStatus = QCOStatus.MANDATORY_QCO
    qco_order_name: Optional[str] = None
    missing_facts: List[str] = Field(default_factory=list)
    conflicting_facts: List[str] = Field(default_factory=list)
    final_status: ApplicabilityState


class ApplicabilityDecision(BaseModel):
    """Structured applicability output separating technical relevance from regulatory mandate."""
    standard_number: str
    standard_title: str
    applicability_status: ApplicabilityState = ApplicabilityState.APPLICABLE
    technical_relevance: str = "APPLICABLE"  # For backwards-compatibility with existing tests
    regulatory_status: str = "VERIFIED_MANDATORY_QCO"
    scope_status: ScopeStatus = ScopeStatus.IN_SCOPE
    qco_status: QCOStatus = QCOStatus.MANDATORY_QCO
    matched_rule_id: str
    rule_verification_status: str = "VERIFIED"
    scheme: str = "Scheme I (ISI Mark)"
    mandatory_reason: Optional[str] = None
    explanation: str
    sources: List[RuleSourceReference] = Field(default_factory=list)
    llm_decision: bool = False  # Strictly 0% LLM decision authority

    # Layer 5 Enhanced Production Fields
    dna_version: Union[int, str] = "v1.0"
    supporting_facts: List[SupportingFact] = Field(default_factory=list)
    missing_facts: List[str] = Field(default_factory=list)
    conflicting_facts: List[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None
    action_required: ApplicabilityAction = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
    decision_trace: Optional[DeterministicDecisionTrace] = None
    is_primary: bool = True
    distinguishing_info: Optional[str] = None
    knowledge_version: str = "v1.2.0-gazette-verified"
    amendment_info: Optional[str] = None
    superseded_by: Optional[str] = None

    # M25.0 Formal Applicability Intelligence Fields
    product_id: Optional[str] = None
    standard_revision: Optional[str] = None
    standard_status: StandardStatus = StandardStatus.ACTIVE
    scope_match: ScopeStatus = ScopeStatus.IN_SCOPE
    product_discriminators: Dict[str, Any] = Field(default_factory=dict)
    required_discriminators: List[str] = Field(default_factory=list)
    qco_conditions: List[str] = Field(default_factory=list)
    conditional_conditions: List[ConditionalRequirementEvaluation] = Field(default_factory=list)
    normative_references: List[NormativeStandardReference] = Field(default_factory=list)
    product_condition_status: ProductConditionStatus = ProductConditionStatus.NOT_CONDITIONAL
    normative_dependency_status: NormativeDependencyStatus = NormativeDependencyStatus.PRIMARY_ONLY
    evidence_availability_status: EvidenceAvailabilityStatus = EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED
    decision_reasons: List[str] = Field(default_factory=list)
    supporting_evidence: List[SupportingFact] = Field(default_factory=list)
    provenance: Optional[str] = "Bureau of Indian Standards (Official Gazette)"
    confidence_metadata: Dict[str, Any] = Field(default_factory=dict)
    expert_review_required: bool = False
    evaluation_order_trace: List[str] = Field(default_factory=list)
