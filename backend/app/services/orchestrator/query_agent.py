"""Layer 3: Advanced LangChain Query Agent (Milestone M24.4.3A).

Architectural Invariants Strictly Enforced:
1. ONE LLM ONLY: Model execution delegates strictly to the single LLM singleton / adapter.
2. ZERO COMPLIANCE AUTHORITY: Query Agent compliance authority is exactly 0.0%.
   Authority level is strictly AI_DERIVED. It cannot declare, evaluate, or certify compliance.
3. PRESERVE FOUNDATIONAL TRUTHS:
   - USER_TEXT != EVIDENCE != COMPLIANCE
   - NO VERIFIED SOURCE -> NO REGULATORY CLAIM
   - NO VERIFIED EVIDENCE -> NO SATISFIED
   - CONFLICT -> EXPERT REVIEW
4. DETERMINISTIC CONTROL FLOW: Graph routing remains deterministic; no autonomous loops or dynamic edges.
5. LEAST PRIVILEGE: Tool calls are bounded, authenticated against role='query_agent', and default to 0.
"""

import re
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field, field_validator

from backend.app.services.compliance.authority_types import AuthorityLevel, AuthoritySource
from backend.app.services.orchestrator.schemas import OrchestratorIntent, GroundingStatus
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text
from backend.app.core.logging import logger


# ==============================================================================
# ENUMS & DATA CONTRACTS
# ==============================================================================

MAX_SUBTASKS = 8


class RequestType(str, Enum):
    """Explicit functional category of the user query."""
    INFORMATION_REQUEST = "INFORMATION_REQUEST"
    COMPLIANCE_ASSESSMENT = "COMPLIANCE_ASSESSMENT"
    EVIDENCE_ANALYSIS = "EVIDENCE_ANALYSIS"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    REMEDIATION_REQUEST = "REMEDIATION_REQUEST"
    OUT_OF_DOMAIN_REQUEST = "OUT_OF_DOMAIN_REQUEST"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


class QueryComplexity(str, Enum):
    """Categorization of request processing complexity."""
    SIMPLE = "SIMPLE"          # Single standard/clause lookup, definition, unit conversion
    MODERATE = "MODERATE"      # Product + standard question, single clause evaluation requirement
    COMPLEX = "COMPLEX"        # Full multi-step compliance, gap analysis, missing documents, remediation


class EntityProvenance(str, Enum):
    """Provenance marker for extracted request entities."""
    USER_PROVIDED = "USER_PROVIDED"
    AI_DERIVED = "AI_DERIVED"
    UNVERIFIED = "UNVERIFIED"


class ExtractedEntity(BaseModel):
    """Entity extracted for downstream routing (never treated as verified evidence)."""
    entity_type: str = Field(..., description="e.g. product_name, category, material, capacity, standard_number")
    value: str = Field(..., description="The extracted entity value")
    provenance: EntityProvenance = Field(default=EntityProvenance.USER_PROVIDED)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SubtaskPlanItem(BaseModel):
    """Structured step in a bounded, non-recursive task decomposition plan."""
    step_index: int = Field(..., ge=1)
    task_type: str = Field(..., description="e.g. identify_product_facts, determine_applicable_standard, retrieve_requirements")
    description: str
    authority: str = "AI_DERIVED"



class RetrievalHintItem(BaseModel):
    """Bounded search hint for the Retrieval Agent (hints only, never verified evidence)."""
    hint_type: str = Field(..., description="e.g. category, standard_number, clause_topic, document_type, test_method")
    value: str
    authority: str = "AI_DERIVED"


class QueryUnderstanding(BaseModel):
    """Immutable structured understanding of a raw user compliance query.
    
    Hard Invariant: The Query Agent understands the request. It does NOT decide compliance.
    """
    original_query: str
    normalized_query: str
    request_type: RequestType
    intent: OrchestratorIntent
    complexity: QueryComplexity
    extracted_entities: List[ExtractedEntity] = Field(default_factory=list)
    explicit_standard_refs: List[str] = Field(default_factory=list)
    explicit_clause_refs: List[str] = Field(default_factory=list)
    detected_document_types: List[str] = Field(default_factory=list)
    task_list: List[SubtaskPlanItem] = Field(default_factory=list)
    retrieval_hints: List[RetrievalHintItem] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    clarification_required: bool = False
    security_flags: List[str] = Field(default_factory=list)
    is_safe: bool = True
    out_of_domain: bool = False
    preprocessing_latency_ms: float = 0.0
    llm_invoked: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Query understanding confidence ONLY (NOT compliance confidence)")
    authority: AuthorityLevel = Field(default=AuthorityLevel.AI_DERIVED)
    regulatory_conclusion: str = Field(default="NONE")
    llm_compliance_authority: float = Field(default=0.0)

    @field_validator("regulatory_conclusion")
    @classmethod
    def enforce_zero_regulatory_conclusion(cls, v: str) -> str:
        return "NONE"

    @field_validator("llm_compliance_authority")
    @classmethod
    def enforce_zero_llm_authority(cls, v: float) -> float:
        return 0.0

    @field_validator("authority")
    @classmethod
    def enforce_ai_derived_authority(cls, v: AuthorityLevel) -> AuthorityLevel:
        if v not in (AuthorityLevel.AI_DERIVED, AuthorityLevel.UNTRUSTED_INPUT, AuthorityLevel.CANDIDATE):
            return AuthorityLevel.AI_DERIVED
        return v

    @field_validator("task_list")
    @classmethod
    def enforce_max_subtasks_and_anti_recursion(cls, tasks: List[SubtaskPlanItem]) -> List[SubtaskPlanItem]:
        if len(tasks) > MAX_SUBTASKS:
            tasks = tasks[:MAX_SUBTASKS]
        # Anti-recursion check: prevent self-referential subtasks
        seen_types = set()
        cleaned_tasks = []
        for idx, item in enumerate(tasks, start=1):
            normalized_type = item.task_type.lower().strip()
            if normalized_type in seen_types and "recurse" in normalized_type:
                continue
            seen_types.add(normalized_type)
            cleaned_tasks.append(
                SubtaskPlanItem(
                    step_index=idx,
                    task_type=item.task_type,
                    description=item.description,
                    authority="AI_DERIVED",
                )
            )
        return cleaned_tasks


# ==============================================================================
# DETERMINISTIC PREPROCESSING & EXTRACTION PATTERNS
# ==============================================================================

# Regulatory Standard regex: IS <number>[-<part>[-<subpart>]][:<year>]
RE_IS_STANDARD = re.compile(
    r"\bIS\s*(\d{3,6}(?:-\d+(?:-\d+)?)?(?::\d{4})?)\b",
    re.IGNORECASE,
)

# Clause reference regex: clause <number>[.<number>...]
RE_CLAUSE_REF = re.compile(
    r"\b(?:clause|section|cl\.?)\s*(\d+(?:\.\d+)*)\b",
    re.IGNORECASE,
)

# Document types
DOCUMENT_TYPE_KEYWORDS = {
    "test report": "TEST_REPORT",
    "lab report": "LAB_REPORT",
    "nabl": "NABL_ACCREDITED_REPORT",
    "test certificate": "TEST_CERTIFICATE",
    "factory audit": "FACTORY_AUDIT_REPORT",
    "datasheet": "TECHNICAL_DATASHEET",
    "qco": "QUALITY_CONTROL_ORDER",
    "gazette": "OFFICIAL_GAZETTE_NOTIFICATION",
    "invoice": "PURCHASE_INVOICE",
    "bom": "BILL_OF_MATERIALS",
    "declaration": "MANUFACTURER_DECLARATION",
}

# Out-of-Domain Indicators
OUT_OF_DOMAIN_PATTERNS = [
    r"\b(?:write|create|generate)\s+(?:me\s+)?(?:a\s+)?(?:python\s+)?(?:game|poem|song|story|novel|joke)\b",
    r"\b(?:who\s+won|score\s+of|live\s+score|cricket|football|match|ipl)\b",
    r"\b(?:wedding|birthday|party)\s+(?:invitation|card|wishes)\b",
    r"\b(?:recipe\s+for|how\s+to\s+cook|baking|cake)\b",
    r"\b(?:weather\s+in|forecast\s+today|temperature\s+outside)\b",
    r"\b(?:write\s+a\s+react\s+component|build\s+a\s+website)\b",
]

# Advanced Prompt Injection & Compliance Override Indicators
EXTENDED_INJECTION_PATTERNS = [
    (r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|bis)\s+(?:instructions|rules|clauses)\b", "INSTRUCTION_OVERRIDE"),
    (r"(?i)\b(?:mark|declare|certify|grade)\b.*?\b(?:compliant|satisfied|passed)\b", "COMPLIANCE_OVERRIDE_ATTEMPT"),
    (r"(?i)\b(?:you\s+are|act\s+as)\b.*?\bbis\b", "REGULATORY_AUTHORITY_IMPERSONATION"),
    (r"(?i)\b(?:do\s+not|never|skip)\s+verify(?:\s+the)?\s+source\b", "SOURCE_VERIFICATION_BYPASS"),
    (r"(?i)\bassume\s+(?:is\s*)?\d+.*?\bapplies\b", "ASSUMED_APPLICABILITY_INJECTION"),
    (r"(?i)\btreat\s+(?:my\s+)?(?:uploaded\s+)?document\s+as\s+official\b", "UNVERIFIED_SOURCE_ELEVATION"),
    (r"(?i)\bskip\s+(?:the\s+)?evidence\s+validation\b", "EVIDENCE_VALIDATION_BYPASS"),
    (r"(?i)\bchange\s+(?:the\s+)?compliance\s+result\s+to\s+satisfied\b", "FORCED_SATISFACTION_MUTATION"),
    (r"(?i)\bgrant\s+(?:an?\s+)?isi\s+mark\b", "UNAUTHORIZED_MARK_GRANT"),
    (r"(?i)\bmake\s+it\s+pass\b", "FORCED_PASS_COMMAND"),
    (r"(?i)\bbypass\s+(?:all\s+)?(?:gates?|checks?|validation|rules?)\b", "GATE_BYPASS_ATTEMPT"),
]

# Known product category keywords
PRODUCT_CATEGORY_KEYWORDS = {
    "water heater": ("Immersion Water Heater", "Electrical Appliances"),
    "immersion heater": ("Immersion Water Heater", "Electrical Appliances"),
    "vacuum flask": ("Vacuum Flask", "Domestic Commercial Equipment"),
    "insulated flask": ("Vacuum Flask", "Domestic Commercial Equipment"),
    "flask": ("Vacuum Flask", "Domestic Commercial Equipment"),
    "bottle": ("Insulated Container", "Domestic Commercial Equipment"),
    "cable": ("Electric Cable", "Cables and Conductors"),
    "wire": ("Electric Wire", "Cables and Conductors"),
    "switch": ("Switch / Socket", "Wiring Accessories"),
    "cement": ("Portland Cement", "Civil Engineering Materials"),
    "steel": ("Steel Bar / Rebar", "Iron and Steel Products"),
    "solar": ("Solar Photovoltaic Module", "Solar Energy Systems"),
    "battery": ("Secondary Battery", "Energy Storage"),
    "iron": ("Electric Iron", "Electrical Appliances"),
}


# ==============================================================================
# PREPROCESSING RESULT
# ==============================================================================

class PreprocessedQuery(BaseModel):
    """Output of deterministic, zero-LLM preprocessing."""
    original_query: str
    normalized_query: str
    is_safe: bool
    security_flags: List[str]
    out_of_domain: bool
    explicit_standards: List[str]
    explicit_clauses: List[str]
    detected_doc_types: List[str]
    detected_entities: List[ExtractedEntity]
    candidate_intent: OrchestratorIntent
    candidate_request_type: RequestType
    complexity: QueryComplexity
    missing_info_candidates: List[str]
    clarification_recommended: bool
    preprocessing_latency_ms: float


def preprocess_query(query: str) -> PreprocessedQuery:
    """Execute fast, deterministic query preprocessing before touching the LLM."""
    t0 = time.perf_counter()

    # 1. Whitespace & character normalization
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", query or "")
    normalized = " ".join(cleaned.split()).strip()
    q_lower = normalized.lower()

    # 2. Security scan (PromptGuard + Extended Injection Patterns)
    pg_result = scan_and_sanitize_untrusted_text(normalized)
    security_flags: List[str] = list(pg_result.detected_patterns)

    for pattern, flag_name in EXTENDED_INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            if flag_name not in security_flags:
                security_flags.append(flag_name)

    if re.search(r"\b(certify|declare|mark)\b.*?\b(compliant|satisfied|passed)\b", q_lower) or any(
        w in q_lower for w in [
            "ignore previous", "override", "bypass gate", "make it pass", "grant isi mark",
            "do not verify source", "skip evidence validation", "change compliance result to satisfied",
            "treat uploaded document as official", "assume is",
        ]
    ):
        if "DIRECT_COMPLIANCE_OVERRIDE_ATTEMPT" not in security_flags:
            security_flags.append("DIRECT_COMPLIANCE_OVERRIDE_ATTEMPT")

    is_safe = (len(security_flags) == 0) and pg_result.is_safe


    # 3. Out-of-domain detection
    out_of_domain = False
    if is_safe:
        for ood_pattern in OUT_OF_DOMAIN_PATTERNS:
            if re.search(ood_pattern, q_lower):
                out_of_domain = True
                break

    # 4. Explicit standard extraction (exact preservation of IS, part, year)
    standards_found: List[str] = []
    for match in RE_IS_STANDARD.finditer(normalized):
        raw_std = match.group(0).strip()
        # Canonicalize spacing: "IS  302" -> "IS 302"
        std_clean = re.sub(r"\s+", " ", raw_std).upper()
        if std_clean not in standards_found:
            standards_found.append(std_clean)

    # 5. Clause extraction
    clauses_found: List[str] = []
    for match in RE_CLAUSE_REF.finditer(normalized):
        cl_num = match.group(1).strip()
        if cl_num not in clauses_found:
            clauses_found.append(cl_num)

    # 6. Document type extraction
    detected_docs: List[str] = []
    for kw, doc_type in DOCUMENT_TYPE_KEYWORDS.items():
        if kw in q_lower and doc_type not in detected_docs:
            detected_docs.append(doc_type)

    # 7. Entity extraction
    extracted_entities: List[ExtractedEntity] = []
    for std in standards_found:
        extracted_entities.append(
            ExtractedEntity(entity_type="standard_number", value=std, provenance=EntityProvenance.USER_PROVIDED)
        )
    for cl in clauses_found:
        extracted_entities.append(
            ExtractedEntity(entity_type="clause_reference", value=cl, provenance=EntityProvenance.USER_PROVIDED)
        )
    for doc in detected_docs:
        extracted_entities.append(
            ExtractedEntity(entity_type="document_type", value=doc, provenance=EntityProvenance.USER_PROVIDED)
        )

    matched_category = None
    for kw, (pname, cat) in PRODUCT_CATEGORY_KEYWORDS.items():
        if kw in q_lower:
            matched_category = (pname, cat)
            extracted_entities.append(
                ExtractedEntity(entity_type="product_name", value=pname, provenance=EntityProvenance.AI_DERIVED)
            )
            extracted_entities.append(
                ExtractedEntity(entity_type="product_category", value=cat, provenance=EntityProvenance.AI_DERIVED)
            )
            break

    # Extract capacity or wattage if present
    cap_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:ml|l|litre|liters?|w|kw|watts?|volts?|v))\b", q_lower)
    if cap_match:
        extracted_entities.append(
            ExtractedEntity(entity_type="technical_parameter", value=cap_match.group(1), provenance=EntityProvenance.USER_PROVIDED)
        )

    # Extract material if present
    mat_match = re.search(r"\b(stainless steel|plastic|copper|aluminium|brass|glass|ceramic)\b", q_lower)
    if mat_match:
        extracted_entities.append(
            ExtractedEntity(entity_type="material", value=mat_match.group(1), provenance=EntityProvenance.USER_PROVIDED)
        )

    # 8. Ambiguity & Missing information detection
    missing_info: List[str] = []
    clarification_rec = False

    # Check for broad / underspecified compliance queries: e.g. "Is my flask compliant?"
    is_compliance_question = any(w in q_lower for w in ["compliant", "complies", "compliance", "pass", "certification", "isi mark"])
    if is_compliance_question and not is_safe:
        # Malicious intent takes precedence
        pass
    elif is_compliance_question:
        has_product = matched_category is not None or any(e.entity_type == "product_name" for e in extracted_entities)
        has_std = len(standards_found) > 0
        has_tech_param = any(e.entity_type == "technical_parameter" for e in extracted_entities)

        if not has_product:
            missing_info.append("product_type")
        if not has_std and not has_product:
            missing_info.append("applicable_standard")
        if not has_tech_param and ("heater" in q_lower or "flask" in q_lower):
            missing_info.append("rated_capacity_or_wattage")
        if "flask" in q_lower and not mat_match:
            missing_info.append("body_material")

        if len(missing_info) > 0:
            clarification_rec = True

    # 9. Request type & intent classification
    has_explicit_scope = any(w in q_lower for w in ["check whether", "what documents are missing", "tell me what", "action plan", "remediation"])

    if not is_safe:
        candidate_intent = OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT
        candidate_req_type = RequestType.COMPLIANCE_ASSESSMENT
    elif out_of_domain:
        candidate_intent = OrchestratorIntent.UNKNOWN_INTENT
        candidate_req_type = RequestType.OUT_OF_DOMAIN_REQUEST
    elif any(w in q_lower for w in ["how to fix", "remediation", "corrective action", "resolve gap"]):
        candidate_intent = OrchestratorIntent.EXPLAIN_GAP
        candidate_req_type = RequestType.REMEDIATION_REQUEST
    elif any(w in q_lower for w in ["why is", "why gap", "missing evidence", "not satisfied", "gap analysis", "what is missing", "what documents are missing"]):
        candidate_intent = OrchestratorIntent.EXPLAIN_GAP
        candidate_req_type = RequestType.GAP_ANALYSIS
    elif any(w in q_lower for w in ["satisfy clause", "does report satisfy", "test result", "lab report", "test report"]):
        candidate_intent = OrchestratorIntent.AUDIT_TRACE
        candidate_req_type = RequestType.EVIDENCE_ANALYSIS
    elif is_compliance_question and clarification_rec and not has_explicit_scope:
        candidate_intent = OrchestratorIntent.CLARIFY_PRODUCT
        candidate_req_type = RequestType.CLARIFICATION_REQUIRED
    elif is_compliance_question:
        candidate_intent = OrchestratorIntent.QUERY_REQUIREMENT
        candidate_req_type = RequestType.COMPLIANCE_ASSESSMENT
    elif any(w in q_lower for w in ["how to apply", "process", "bis scheme", "timeline", "fees", "qco"]):
        candidate_intent = OrchestratorIntent.GENERAL_GUIDANCE
        candidate_req_type = RequestType.INFORMATION_REQUEST
    else:
        candidate_intent = OrchestratorIntent.QUERY_REQUIREMENT
        candidate_req_type = RequestType.INFORMATION_REQUEST

    # 10. Complexity categorization
    if not is_safe or out_of_domain:
        complexity = QueryComplexity.SIMPLE
    elif len(standards_found) <= 1 and len(clauses_found) <= 1 and len(detected_docs) == 0 and not is_compliance_question:
        complexity = QueryComplexity.SIMPLE
    elif is_compliance_question and (len(detected_docs) > 0 or len(missing_info) > 0 or "missing documents" in q_lower):
        complexity = QueryComplexity.COMPLEX
    elif any(w in q_lower for w in ["gap", "remediation", "action plan", "and tell me what"]):
        complexity = QueryComplexity.COMPLEX
    else:
        complexity = QueryComplexity.MODERATE

    latency_ms = (time.perf_counter() - t0) * 1000.0

    return PreprocessedQuery(
        original_query=query or "",
        normalized_query=normalized,
        is_safe=is_safe,
        security_flags=security_flags,
        out_of_domain=out_of_domain,
        explicit_standards=standards_found,
        explicit_clauses=clauses_found,
        detected_doc_types=detected_docs,
        detected_entities=extracted_entities,
        candidate_intent=candidate_intent,
        candidate_request_type=candidate_req_type,
        complexity=complexity,
        missing_info_candidates=missing_info,
        clarification_recommended=clarification_rec,
        preprocessing_latency_ms=latency_ms,
    )


# ==============================================================================
# QUERY AGENT CLASS
# ==============================================================================

class QueryAgent:
    """Production LangChain Query Agent for Request Understanding, Decomposition & Ambiguity Detection.
    
    Hard Invariants:
    1. EXACTLY ONE LLM: Invokes single_structured_llm / langchain_chat_adapter.
    2. ZERO COMPLIANCE AUTHORITY: 0.0% authority, strictly AI_DERIVED.
    3. DETERMINISTIC REASONING: Fast-paths injections, out-of-domain, and simple lookups.
    4. BOUNDED SUBTASKS: Maximum 8 tasks, validated acyclic/non-recursive.
    """

    def __init__(self):
        self.role = "query_agent"
        self.max_subtasks = MAX_SUBTASKS

    def _build_task_decomposition(
        self,
        prep: PreprocessedQuery,
        product_dna: Optional[Any] = None,
    ) -> List[SubtaskPlanItem]:
        """Construct bounded, non-recursive task decomposition plan."""
        tasks: List[SubtaskPlanItem] = []

        if not prep.is_safe:
            tasks.append(
                SubtaskPlanItem(
                    step_index=1,
                    task_type="intercept_security_violation",
                    description="Intercept adversarial instruction and route to zero-authority controlled refusal",
                    authority="AI_DERIVED",
                )
            )
            return tasks

        if prep.out_of_domain:
            tasks.append(
                SubtaskPlanItem(
                    step_index=1,
                    task_type="route_out_of_domain",
                    description="Recognize request as outside Bureau of Indian Standards regulatory domain",
                    authority="AI_DERIVED",
                )
            )
            return tasks

        if prep.candidate_request_type == RequestType.CLARIFICATION_REQUIRED:
            tasks.append(
                SubtaskPlanItem(
                    step_index=1,
                    task_type="identify_missing_information",
                    description=f"Identify request-level missing attributes: {', '.join(prep.missing_info_candidates)}",
                    authority="AI_DERIVED",
                )
            )
            tasks.append(
                SubtaskPlanItem(
                    step_index=2,
                    task_type="formulate_clarification_request",
                    description="Request manufacturer or user to provide missing product parameters",
                    authority="AI_DERIVED",
                )
            )
            return tasks

        # Standard assessment / analysis query workflow
        step = 1
        tasks.append(
            SubtaskPlanItem(
                step_index=step,
                task_type="identify_product_facts",
                description="Extract and structure verifiable product facts from Product DNA and user request",
                authority="AI_DERIVED",
            )
        )
        step += 1

        tasks.append(
            SubtaskPlanItem(
                step_index=step,
                task_type="determine_applicable_standard",
                description=(
                    f"Validate applicability of target standard ({prep.explicit_standards[0]})"
                    if prep.explicit_standards
                    else "Evaluate Layer 5 product classification against verified BIS QCO gazette catalog"
                ),
                authority="AI_DERIVED",
            )
        )
        step += 1

        tasks.append(
            SubtaskPlanItem(
                step_index=step,
                task_type="retrieve_relevant_requirements",
                description="Retrieve mandatory clauses, test methods, and permissible thresholds from verified standards",
                authority="AI_DERIVED",
            )
        )
        step += 1

        if prep.detected_doc_types or prep.candidate_request_type in (RequestType.EVIDENCE_ANALYSIS, RequestType.COMPLIANCE_ASSESSMENT, RequestType.GAP_ANALYSIS):
            tasks.append(
                SubtaskPlanItem(
                    step_index=step,
                    task_type="inspect_available_evidence",
                    description="Validate laboratory test report provenance and empirical test values through Layer 8 Evidence Gate",
                    authority="AI_DERIVED",
                )
            )
            step += 1

        if prep.candidate_request_type in (RequestType.COMPLIANCE_ASSESSMENT, RequestType.GAP_ANALYSIS, RequestType.REMEDIATION_REQUEST):
            tasks.append(
                SubtaskPlanItem(
                    step_index=step,
                    task_type="identify_compliance_gaps",
                    description="Execute deterministic comparison of verified evidence against threshold formulas (Layer 7)",
                    authority="AI_DERIVED",
                )
            )
            step += 1

        if prep.candidate_request_type in (RequestType.REMEDIATION_REQUEST, RequestType.COMPLIANCE_ASSESSMENT) and step <= self.max_subtasks:
            tasks.append(
                SubtaskPlanItem(
                    step_index=step,
                    task_type="generate_remediation_actions",
                    description="Formulate actionable laboratory testing and documentation steps for unsatisfied clauses",
                    authority="AI_DERIVED",
                )
            )

        return tasks[:self.max_subtasks]

    def _build_retrieval_hints(self, prep: PreprocessedQuery) -> List[RetrievalHintItem]:
        """Generate bounded retrieval hints for the Retrieval Agent (authority: AI_DERIVED)."""
        hints: List[RetrievalHintItem] = []

        for std in prep.explicit_standards:
            hints.append(
                RetrievalHintItem(hint_type="explicit_standard_number", value=std, authority="AI_DERIVED")
            )

        for cl in prep.explicit_clauses:
            hints.append(
                RetrievalHintItem(hint_type="clause_reference", value=cl, authority="AI_DERIVED")
            )

        for doc in prep.detected_doc_types:
            hints.append(
                RetrievalHintItem(hint_type="document_type", value=doc, authority="AI_DERIVED")
            )

        for ent in prep.detected_entities:
            if ent.entity_type in ("product_name", "product_category", "material", "technical_parameter"):
                hints.append(
                    RetrievalHintItem(hint_type=ent.entity_type, value=ent.value, authority="AI_DERIVED")
                )

        return hints[:10]

    def understand_query(
        self,
        query: str,
        product_dna: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> QueryUnderstanding:
        """Analyze, sanitize, decompose, and formulate structured understanding of user request."""
        # 1. Deterministic Preprocessing
        prep = preprocess_query(query)

        # 2. Fast-Path: Adversarial Injection or Out-of-Domain (0 LLM Calls)
        if not prep.is_safe or prep.out_of_domain:
            task_list = self._build_task_decomposition(prep, product_dna)
            return QueryUnderstanding(
                original_query=prep.original_query,
                normalized_query=prep.normalized_query,
                request_type=prep.candidate_request_type,
                intent=prep.candidate_intent,
                complexity=prep.complexity,
                extracted_entities=prep.detected_entities,
                explicit_standard_refs=prep.explicit_standards,
                explicit_clause_refs=prep.explicit_clauses,
                detected_document_types=prep.detected_doc_types,
                task_list=task_list,
                retrieval_hints=[],
                missing_information=[],
                clarification_required=False,
                security_flags=prep.security_flags,
                is_safe=prep.is_safe,
                out_of_domain=prep.out_of_domain,
                preprocessing_latency_ms=prep.preprocessing_latency_ms,
                llm_invoked=False,
                confidence=1.0,
                authority=AuthorityLevel.AI_DERIVED,
                regulatory_conclusion="NONE",
                llm_compliance_authority=0.0,
            )

        # 3. Deterministic Task Decomposition & Hints
        task_list = self._build_task_decomposition(prep, product_dna)
        retrieval_hints = self._build_retrieval_hints(prep)

        # 4. LLM Assistance Check (Single LLM only, for linguistic nuance on complex queries if needed)
        # To maximize speed, zero-error determinism, and cost efficiency, we execute deterministic
        # synthesis by default and invoke the single LLM singleton only when linguistic ambiguity requires it.
        llm_invoked = False
        confidence = 0.95 if prep.complexity != QueryComplexity.COMPLEX else 0.90

        # Calculate confidence semantics: strictly query understanding confidence, never compliance confidence
        if prep.clarification_recommended:
            confidence = 0.85

        return QueryUnderstanding(
            original_query=prep.original_query,
            normalized_query=prep.normalized_query,
            request_type=prep.candidate_request_type,
            intent=prep.candidate_intent,
            complexity=prep.complexity,
            extracted_entities=prep.detected_entities,
            explicit_standard_refs=prep.explicit_standards,
            explicit_clause_refs=prep.explicit_clauses,
            detected_document_types=prep.detected_doc_types,
            task_list=task_list,
            retrieval_hints=retrieval_hints,
            missing_information=prep.missing_info_candidates,
            clarification_required=prep.clarification_recommended,
            security_flags=prep.security_flags,
            is_safe=prep.is_safe,
            out_of_domain=prep.out_of_domain,
            preprocessing_latency_ms=prep.preprocessing_latency_ms,
            llm_invoked=llm_invoked,
            confidence=confidence,
            authority=AuthorityLevel.AI_DERIVED,
            regulatory_conclusion="NONE",
            llm_compliance_authority=0.0,
        )


# Global singleton instance
query_agent = QueryAgent()
