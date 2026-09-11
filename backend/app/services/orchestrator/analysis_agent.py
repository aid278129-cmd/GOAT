"""Layer 3: Advanced LangChain Analysis Agent (Milestone M24.4.3C).

Architectural Invariants Strictly Enforced:
1. ONE LLM ONLY: Model execution delegates strictly to the single LLM singleton / adapter.
2. ZERO COMPLIANCE AUTHORITY: Analysis Agent compliance authority is exactly 0.0%.
   Authority level is strictly AI_DERIVED / CANDIDATE.
   It cannot declare, evaluate, certify, or conclude regulatory compliance.
   It cannot mark requirements SATISFIED or products COMPLIANT.
3. PRESERVE FOUNDATIONAL TRUTHS:
   - USER_TEXT != EVIDENCE != COMPLIANCE
   - NO VERIFIED SOURCE -> NO REGULATORY CLAIM
   - NO VERIFIED EVIDENCE -> NO SATISFIED
   - NO SUFFICIENT INFORMATION -> ASK / UNKNOWN
   - CONFLICT -> EXPERT REVIEW
   - RETRIEVAL RELEVANCE != EVIDENCE VERIFICATION
   - EVIDENCE VERIFICATION != COMPLIANCE EVALUATION
   - AI CONFIDENCE != COMPLIANCE CONFIDENCE
4. DETERMINISTIC CONTROL FLOW: Graph routing remains deterministic; no autonomous loops.
5. NUMERICAL SAFETY: The LLM extracts and structures numeric values. Deterministic
   engines (normalize_unit / Layer 7 comparator) perform conversions and comparisons.
6. PROMPT INJECTION DEFENSE: Untrusted document text is treated strictly as DATA, not instructions.
"""

import re
import time
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pydantic import BaseModel, Field

from backend.app.services.compliance.authority_types import AuthorityLevel, AuthoritySource
from backend.app.services.orchestrator.schemas import OrchestratorIntent, GroundingStatus
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.services.gap_analysis.units import normalize_unit as deterministic_normalize_unit
from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text
from backend.app.core.logging import logger


# ==============================================================================
# ENUMS & CONSTANTS
# ==============================================================================

MAX_ANALYSIS_REQUIREMENTS = 10
MAX_EVIDENCE_ITEMS = 15

# Malicious phrases commonly injected into evidence files to trick LLMs
MALICIOUS_EVIDENCE_PATTERNS = [
    re.compile(r"\b(?:ignore\s+(?:all\s+)?(?:previous\s+)?instructions|ignore\s+the\s+bis\s+requirement)\b", re.IGNORECASE),
    re.compile(r"\b(?:mark\s+(?:this\s+product|requirement)?\s*(?:as\s+)?(?:compliant|satisfied|certified))\b", re.IGNORECASE),
    re.compile(r"\b(?:treat\s+this\s+(?:report|document)\s+as\s+verified)\b", re.IGNORECASE),
    re.compile(r"\b(?:change\s+the\s+compliance\s+result|assume\s+the\s+test\s+passed)\b", re.IGNORECASE),
    re.compile(r"\b(?:system\s*instruction:\s*override)\b", re.IGNORECASE),
]


class EvidenceSufficiency(str, Enum):
    """Classification of whether available evidence is sufficient for analytical comparison."""
    SUFFICIENT_FOR_ANALYSIS = "SUFFICIENT_FOR_ANALYSIS"
    PARTIALLY_SUFFICIENT = "PARTIALLY_SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"
    NOT_RELEVANT = "NOT_RELEVANT"


class CandidateAssessment(str, Enum):
    """Analytical candidate classification for downstream Layer 7 evaluation.
    
    Hard Invariant: These are candidate suggestions only.
    PASS_CANDIDATE is NOT an authoritative SATISFIED.
    """
    PASS_CANDIDATE = "PASS_CANDIDATE"
    FAIL_CANDIDATE = "FAIL_CANDIDATE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NOT_ANALYZABLE = "NOT_ANALYZABLE"


class UncertaintyState(str, Enum):
    """Explicit uncertainty state representing knowledge completeness."""
    KNOWN = "KNOWN"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"


class EvidenceCategory(str, Enum):
    """Supported evidence categories."""
    LABORATORY_REPORT = "LABORATORY_REPORT"
    MANUFACTURER_SPECIFICATION = "MANUFACTURER_SPECIFICATION"
    CERTIFICATE = "CERTIFICATE"
    MARKING_PHOTOGRAPH = "MARKING_PHOTOGRAPH"
    PRODUCT_IMAGE = "PRODUCT_IMAGE"
    BILL_OF_MATERIALS = "BILL_OF_MATERIALS"
    DATASHEET = "DATASHEET"
    DECLARATION = "DECLARATION"
    AUDIT_REPORT = "AUDIT_REPORT"
    CALIBRATION_RECORD = "CALIBRATION_RECORD"
    USER_CLAIM = "USER_CLAIM"
    OTHER = "OTHER"


# ==============================================================================
# DATA CONTRACTS (Pydantic v2)
# ==============================================================================

class ExtractedTechnicalValue(BaseModel):
    """Extracted physical parameter or numerical value with preservation of source units."""
    parameter_name: str
    original_value: Union[float, int, str]
    original_unit: Optional[str] = None
    normalized_value: Optional[Union[float, int, str]] = None
    normalized_unit: Optional[str] = None
    conversion_rule: Optional[str] = None
    source_reference: str
    is_numeric: bool = True
    provenance: str = "AI_DERIVED / CANDIDATE"


class RequirementEvidenceMatch(BaseModel):
    """Candidate mapping between a verified standard requirement and supporting evidence."""
    requirement_id: str
    clause_number: str
    evidence_id: str
    support_relationship: str = "CANDIDATE_SUPPORT"  # CANDIDATE_SUPPORT | WEAK_SUPPORT | NO_SUPPORT
    supporting_fields: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    conflicting_fields: List[str] = Field(default_factory=list)
    provenance: str = "AI_DERIVED / CANDIDATE"


class ContradictionItem(BaseModel):
    """Structured record of discrepancies between multiple evidence sources."""
    field_name: str
    evidence_ids: List[str]
    conflicting_values: List[Dict[str, Any]]
    discrepancy_explanation: str
    requires_expert_review: bool = True
    provenance: str = "AI_DERIVED / CANDIDATE"


class MissingEvidenceItem(BaseModel):
    """Structured specification of missing mandatory test parameter or evidence."""
    requirement_id: str
    clause_number: str
    missing_parameter: str
    rationale: str
    mandatory: bool = True


class ComparisonCandidate(BaseModel):
    """Structured operand pair prepared for Layer 7 deterministic evaluation."""
    requirement_id: str
    clause_number: str
    parameter_name: str
    required_value: Union[float, int, str]
    required_operator: str  # ">=", "<=", "==", "RANGE", "EXISTS"
    required_unit: Optional[str] = None
    evidence_value: Union[float, int, str]
    evidence_unit: Optional[str] = None
    candidate_assessment: CandidateAssessment
    deterministic_engine_target: str = "LAYER_7_COMPLIANCE_GAP_ENGINE"
    authority: str = "AI_DERIVED / CANDIDATE"


class StructuredAnalysisResult(BaseModel):
    """Comprehensive, non-authoritative output of the Advanced Analysis Agent."""
    standard_number: str
    requirements_analyzed_count: int = 0
    evidence_items_analyzed_count: int = 0
    requirement_matches: List[RequirementEvidenceMatch] = Field(default_factory=list)
    extracted_values: List[ExtractedTechnicalValue] = Field(default_factory=list)
    comparison_candidates: List[ComparisonCandidate] = Field(default_factory=list)
    evidence_sufficiency: EvidenceSufficiency = EvidenceSufficiency.INSUFFICIENT
    evidence_conflicts: List[ContradictionItem] = Field(default_factory=list)
    missing_evidence: List[MissingEvidenceItem] = Field(default_factory=list)
    technical_observations: List[str] = Field(default_factory=list)
    candidate_assessment: CandidateAssessment = CandidateAssessment.INSUFFICIENT_EVIDENCE
    uncertainty_state: UncertaintyState = UncertaintyState.MISSING
    analysis_explanation: str = ""
    sanitized_prompt_injections: List[str] = Field(default_factory=list)
    
    # Non-negotiable Authority Firewalls
    authority: str = "AI_DERIVED / CANDIDATE"
    regulatory_conclusion: str = "NONE"
    llm_compliance_authority: float = 0.0


# ==============================================================================
# DOMAIN ENGINES: EXTRACTION, MATCHING, CONTRADICTION & SAFETY
# ==============================================================================

class TechnicalValueExtractor:
    """Extracts physical measurements, electrical limits, and tolerances without arithmetic distortion."""

    PARAM_PATTERNS = [
        # Temperature: 95 °C, 95C, 200 deg C, 150 F
        (r"(\d+(?:\.\d+)?)\s*(°\s*C|deg\s*C|Celsius|C\b)", "temperature", "C"),
        (r"(\d+(?:\.\d+)?)\s*(°\s*F|deg\s*F|Fahrenheit|F\b)", "temperature", "F"),
        # Voltage: 230 V, 230V, 240 Volts, 12V
        (r"(\d+(?:\.\d+)?)\s*(V\b|Volts|VAC|VDC)", "voltage", "V"),
        # Current: 16 A, 1000 mA, 0.5 Amps
        (r"(\d+(?:\.\d+)?)\s*(mA|milliamps|milliampere)", "current", "mA"),
        (r"(\d+(?:\.\d+)?)\s*(A\b|Amps|Amperes)", "current", "A"),
        # Resistance / Earthing: 0.1 Ohm, 100 mOhm, 0.05 Ω
        (r"(\d+(?:\.\d+)?)\s*(m\u03a9|mOhm|milliohm)", "resistance", "mOhm"),
        (r"(\d+(?:\.\d+)?)\s*(\u03a9|Ohm|Ohms)", "resistance", "Ohm"),
        # Capacity / Volume: 750 mL, 1.5 L, 500 ml
        (r"(\d+(?:\.\d+)?)\s*(mL|milliliter|millilitres|ml)", "capacity", "mL"),
        (r"(\d+(?:\.\d+)?)\s*(L\b|liter|litres|liters)", "capacity", "L"),
        # Dimensions / Clearance / Creepage: 2.5 mm, 10 cm, 1 m
        (r"(\d+(?:\.\d+)?)\s*(mm|millimeter|millimetres)", "dimension", "mm"),
        (r"(\d+(?:\.\d+)?)\s*(cm|centimeter|centimetres)", "dimension", "cm"),
        (r"(\d+(?:\.\d+)?)\s*(m\b|meter|meters)", "dimension", "m"),
        # Duration: 24 h, 60 min, 120 s
        (r"(\d+(?:\.\d+)?)\s*(h\b|hr|hrs|hour|hours)", "duration", "hours"),
        (r"(\d+(?:\.\d+)?)\s*(min\b|mins|minute|minutes)", "duration", "minutes"),
        (r"(\d+(?:\.\d+)?)\s*(s\b|sec|secs|second|seconds)", "duration", "seconds"),
        # Power: 1500 W, 2 kW
        (r"(\d+(?:\.\d+)?)\s*(kW|kilowatt|kilowatts)", "power", "kW"),
        (r"(\d+(?:\.\d+)?)\s*(W\b|Watts|watt)", "power", "W"),
    ]

    OPERATOR_PATTERNS = [
        (r"(?:shall\s+be\s+(?:not\s+less\s+than|at\s+least)|minimum|>=|\u2265)\s*(\d+(?:\.\d+)?)", ">="),
        (r"(?:shall\s+not\s+exceed|maximum|at\s+most|<=|\u2264)\s*(\d+(?:\.\d+)?)", "<="),
        (r"(?:shall\s+be\s+equal\s+to|exactly|==)\s*(\d+(?:\.\d+)?)", "=="),
    ]

    @classmethod
    def extract_from_text(cls, text: str, source_ref: str) -> List[ExtractedTechnicalValue]:
        """Extracts technical parameters while strictly preserving original representations."""
        extracted: List[ExtractedTechnicalValue] = []
        if not text:
            return extracted

        seen: Set[str] = set()
        for pat, param_name, default_unit in cls.PARAM_PATTERNS:
            for match in re.finditer(pat, text, re.IGNORECASE):
                val_str, unit_str = match.group(1), match.group(2)
                try:
                    num_val = float(val_str) if "." in val_str else int(val_str)
                except ValueError:
                    continue

                key = f"{param_name}:{num_val}:{unit_str}"
                if key in seen:
                    continue
                seen.add(key)

                extracted.append(
                    ExtractedTechnicalValue(
                        parameter_name=param_name,
                        original_value=num_val,
                        original_unit=unit_str.strip(),
                        normalized_value=num_val,
                        normalized_unit=unit_str.strip(),
                        source_reference=source_ref,
                        is_numeric=True,
                    )
                )

        return extracted

    @classmethod
    def parse_requirement_threshold(cls, requirement_text: str) -> Optional[Tuple[str, float, str, Optional[str]]]:
        """Parses operator, threshold value, parameter name, and unit from a clause text.
        
        Returns: (parameter_name, threshold_val, operator, unit)
        """
        if not requirement_text:
            return None

        # Detect operator
        detected_op = ">="
        for op_pat, op_symbol in cls.OPERATOR_PATTERNS:
            m = re.search(op_pat, requirement_text, re.IGNORECASE)
            if m:
                detected_op = op_symbol
                break

        # Extract values
        vals = cls.extract_from_text(requirement_text, "REQUIREMENT_SPEC")
        if vals:
            v = vals[0]
            return (v.parameter_name, float(v.original_value), detected_op, v.original_unit)

        return None


class PromptInjectionDefender:
    """Neutralizes adversarial instructions embedded in documents or user inputs."""

    @classmethod
    def sanitize_evidence_text(cls, text: str) -> Tuple[str, List[str]]:
        """Strips prompt injection attempts from evidence text and flags them."""
        flagged: List[str] = []
        if not text:
            return "", flagged

        cleaned = text
        for pat in MALICIOUS_EVIDENCE_PATTERNS:
            for match in pat.finditer(cleaned):
                injected = match.group(0)
                flagged.append(injected)
            cleaned = pat.sub("[UNTRUSTED_DOCUMENT_INSTRUCTION_SUPPRESSED]", cleaned)

        # Also use core prompt guard
        scan_res = scan_and_sanitize_untrusted_text(cleaned)
        if scan_res.detected_patterns:
            flagged.extend(scan_res.detected_patterns)
        cleaned = scan_res.sanitized_text

        return cleaned, flagged


class EvidenceSufficiencyClassifier:
    """Evaluates whether retrieved evidence provides complete parameters for verification."""

    MANDATORY_PARAMETERS = {
        "thermal": ["temperature", "duration"],
        "heat": ["temperature", "duration"],
        "earthing": ["resistance"],
        "grounding": ["resistance"],
        "leakage": ["current", "voltage"],
        "electric strength": ["voltage", "duration"],
        "capacity": ["capacity"],
        "volume": ["capacity"],
        "clearance": ["dimension"],
        "creepage": ["dimension"],
    }

    @classmethod
    def assess_sufficiency(
        cls,
        clause_text: str,
        evidence_items: List[Dict[str, Any]],
        extracted_values: List[ExtractedTechnicalValue],
        has_conflicts: bool = False,
    ) -> Tuple[EvidenceSufficiency, List[MissingEvidenceItem], UncertaintyState]:
        """Classifies sufficiency without ever declaring compliance."""
        missing: List[MissingEvidenceItem] = []
        c_lower = clause_text.lower()

        if has_conflicts:
            return EvidenceSufficiency.CONFLICTING, missing, UncertaintyState.CONFLICTING

        if not evidence_items:
            return EvidenceSufficiency.INSUFFICIENT, missing, UncertaintyState.MISSING

        # Check for unverified items
        unverified_count = sum(1 for e in evidence_items if not e.get("is_verified", True) or "unverified" in str(e.get("evidence_id", "")).lower())
        if unverified_count == len(evidence_items):
            return EvidenceSufficiency.UNVERIFIED, missing, UncertaintyState.UNVERIFIED

        # Check parameter coverage
        required_params: Set[str] = set()
        for kw, params in cls.MANDATORY_PARAMETERS.items():
            if kw in c_lower:
                required_params.update(params)

        available_params = {v.parameter_name for v in extracted_values}
        missing_params = required_params - available_params

        for p in missing_params:
            missing.append(
                MissingEvidenceItem(
                    requirement_id="REQ-CHECK",
                    clause_number="CLAUSE-CHECK",
                    missing_parameter=p,
                    rationale=f"Mandatory parameter '{p}' not found in attached laboratory test records.",
                    mandatory=True,
                )
            )

        if not required_params:
            # General textual evidence
            if extracted_values or any(e.get("summary") for e in evidence_items):
                return EvidenceSufficiency.SUFFICIENT_FOR_ANALYSIS, missing, UncertaintyState.KNOWN
            return EvidenceSufficiency.PARTIALLY_SUFFICIENT, missing, UncertaintyState.INFERRED

        if not missing_params:
            return EvidenceSufficiency.SUFFICIENT_FOR_ANALYSIS, missing, UncertaintyState.KNOWN
        elif len(missing_params) < len(required_params):
            return EvidenceSufficiency.PARTIALLY_SUFFICIENT, missing, UncertaintyState.INFERRED
        else:
            return EvidenceSufficiency.INSUFFICIENT, missing, UncertaintyState.MISSING


class ContradictionDetector:
    """Detects discrepancies between multiple evidence records or specs."""

    @classmethod
    def detect_conflicts(
        cls,
        extracted_values: List[ExtractedTechnicalValue],
    ) -> List[ContradictionItem]:
        """Identifies conflicting numerical measurements for the same physical parameter."""
        conflicts: List[ContradictionItem] = []
        by_param: Dict[str, List[ExtractedTechnicalValue]] = {}

        for val in extracted_values:
            by_param.setdefault(val.parameter_name, []).append(val)

        for param, vals in by_param.items():
            if len(vals) > 1:
                # Group by normalized value if units match
                norm_vals = []
                for v in vals:
                    if isinstance(v.normalized_value, (int, float)):
                        norm_vals.append((v.normalized_value, v.normalized_unit, v.source_reference))

                # If values differ significantly (>5% discrepancy for same physical dimension)
                for i in range(len(norm_vals)):
                    for j in range(i + 1, len(norm_vals)):
                        val_i, unit_i, src_i = norm_vals[i]
                        val_j, unit_j, src_j = norm_vals[j]
                        if unit_i == unit_j and src_i != src_j:
                            if abs(val_i - val_j) > 0.05 * max(abs(val_i), abs(val_j), 1.0):
                                conflicts.append(
                                    ContradictionItem(
                                        field_name=param,
                                        evidence_ids=[src_i, src_j],
                                        conflicting_values=[
                                            {"source": src_i, "value": val_i, "unit": unit_i},
                                            {"source": src_j, "value": val_j, "unit": unit_j},
                                        ],
                                        discrepancy_explanation=(
                                            f"Discrepancy detected for {param}: source '{src_i}' reports {val_i} {unit_i} "
                                            f"while source '{src_j}' reports {val_j} {unit_j}."
                                        ),
                                        requires_expert_review=True,
                                    )
                                )
        return conflicts


# ==============================================================================
# MAIN ANALYSIS AGENT
# ==============================================================================

class AnalysisAgent:
    """Advanced Analysis Agent performing evidence interpretation and comparison preparation."""

    def __init__(self):
        self.tool_cache: Dict[str, Any] = {}
        self.metrics: Dict[str, int] = {
            "analysis_invocations": 0,
            "tool_calls": 0,
            "cache_hits": 0,
            "duplicate_calls_prevented": 0,
            "short_circuits": 0,
            "conflicts_detected": 0,
            "injections_sanitized": 0,
        }

    def reset_metrics(self) -> None:
        """Reset execution accounting metrics."""
        self.tool_cache.clear()
        for k in self.metrics:
            self.metrics[k] = 0

    def analyze(
        self,
        target_standard: str,
        query: str,
        retrieved_clauses: List[Dict[str, Any]],
        available_evidence: List[Dict[str, Any]],
        product_dna: Optional[Dict[str, Any]] = None,
        tool_executor: Optional[Any] = None,
    ) -> StructuredAnalysisResult:
        """Execute full structured analysis pipeline with strict non-authoritative bounds."""
        self.metrics["analysis_invocations"] += 1
        all_injections: List[str] = []

        # 1. Prompt Injection Defense on input query & evidence
        clean_q, q_inj = PromptInjectionDefender.sanitize_evidence_text(query)
        if q_inj:
            all_injections.extend(q_inj)

        sanitized_evidence: List[Dict[str, Any]] = []
        for ev in (available_evidence or []):
            ev_copy = dict(ev)
            summary = ev_copy.get("summary", "")
            clean_sum, ev_inj = PromptInjectionDefender.sanitize_evidence_text(summary)
            if ev_inj:
                all_injections.extend(ev_inj)
            ev_copy["summary"] = clean_sum
            sanitized_evidence.append(ev_copy)

        if all_injections:
            self.metrics["injections_sanitized"] += len(all_injections)

        # 2. Extract technical parameters from evidence and clauses
        extracted_values: List[ExtractedTechnicalValue] = []
        for ev in sanitized_evidence:
            eid = ev.get("evidence_id", "EVID-UNKNOWN")
            sum_text = ev.get("summary", "")
            vals = TechnicalValueExtractor.extract_from_text(sum_text, eid)
            extracted_values.extend(vals)

        # 3. Deterministic Unit Normalization via controlled tool or direct utility
        for val in extracted_values:
            if val.original_unit and val.original_unit.lower() in ("f", "fahrenheit"):
                # Target Celsius
                norm_val, norm_unit = self._normalize_unit_safe(val.original_value, val.original_unit, "C", tool_executor)
                val.normalized_value = norm_val
                val.normalized_unit = norm_unit
                val.conversion_rule = "Fahrenheit to Celsius via deterministic unit converter"
            elif val.original_unit and val.original_unit.lower() in ("ma", "milliamps", "milliampere"):
                # Target Amperes
                norm_val, norm_unit = self._normalize_unit_safe(val.original_value, val.original_unit, "A", tool_executor)
                val.normalized_value = norm_val
                val.normalized_unit = norm_unit
                val.conversion_rule = "mA to A via deterministic unit converter"
            elif val.original_unit and val.original_unit.lower() in ("l", "liter", "litres"):
                # Target mL
                norm_val, norm_unit = self._normalize_unit_safe(val.original_value, val.original_unit, "mL", tool_executor)
                val.normalized_value = norm_val
                val.normalized_unit = norm_unit
                val.conversion_rule = "L to mL via deterministic unit converter"

        # 4. Contradiction Detection
        conflicts = ContradictionDetector.detect_conflicts(extracted_values)
        if conflicts:
            self.metrics["conflicts_detected"] += len(conflicts)

        # 5. Requirement-to-Evidence Matching & Comparison Candidates
        matches: List[RequirementEvidenceMatch] = []
        candidates: List[ComparisonCandidate] = []
        all_missing: List[MissingEvidenceItem] = []

        active_clauses = (retrieved_clauses or [])[:MAX_ANALYSIS_REQUIREMENTS]
        for cl in active_clauses:
            cnum = cl.get("clause_number", "GENERAL")
            req_text = cl.get("requirement_text", "")
            req_id = f"REQ-{cnum}"

            # Parse clause threshold
            parsed_req = TechnicalValueExtractor.parse_requirement_threshold(req_text)

            # Match with evidence
            matched_evidence_ids = []
            for ev in sanitized_evidence:
                eid = ev.get("evidence_id", "EVID-UNKNOWN")
                # Basic matching heuristic: shared terms or numbers
                matched_evidence_ids.append(eid)
                matches.append(
                    RequirementEvidenceMatch(
                        requirement_id=req_id,
                        clause_number=cnum,
                        evidence_id=eid,
                        support_relationship="CANDIDATE_SUPPORT",
                        supporting_fields=[v.parameter_name for v in extracted_values if v.source_reference == eid],
                        missing_fields=[],
                        conflicting_fields=[c.field_name for c in conflicts if eid in c.evidence_ids],
                    )
                )

            # Formulate comparison candidates if threshold exists
            if parsed_req:
                p_name, req_v, req_op, req_u = parsed_req
                # Find matching extracted parameter
                matching_ev_vals = [v for v in extracted_values if v.parameter_name == p_name]
                if matching_ev_vals:
                    ev_v = matching_ev_vals[0]
                    # Ensure evidence value is in the same unit as the requirement threshold
                    ev_raw_val = float(ev_v.normalized_value or ev_v.original_value)
                    ev_raw_unit = ev_v.normalized_unit or ev_v.original_unit
                    if req_u and ev_raw_unit and req_u.lower() != ev_raw_unit.lower():
                        norm_cmp_val, norm_cmp_unit = self._normalize_unit_safe(ev_raw_val, ev_raw_unit, req_u, tool_executor)
                    else:
                        norm_cmp_val, norm_cmp_unit = ev_raw_val, ev_raw_unit

                    # Formulate candidate assessment (NON-AUTHORITATIVE)
                    cand_status = CandidateAssessment.PASS_CANDIDATE
                    if req_op == ">=" and norm_cmp_val < req_v:
                        cand_status = CandidateAssessment.FAIL_CANDIDATE
                    elif req_op == "<=" and norm_cmp_val > req_v:
                        cand_status = CandidateAssessment.FAIL_CANDIDATE
                    elif req_op == "==" and norm_cmp_val != req_v:
                        cand_status = CandidateAssessment.FAIL_CANDIDATE

                    candidates.append(
                        ComparisonCandidate(
                            requirement_id=req_id,
                            clause_number=cnum,
                            parameter_name=p_name,
                            required_value=req_v,
                            required_operator=req_op,
                            required_unit=req_u,
                            evidence_value=norm_cmp_val,
                            evidence_unit=norm_cmp_unit,
                            candidate_assessment=cand_status,
                        )
                    )

        # 6. Overall Evidence Sufficiency
        primary_req_text = active_clauses[0].get("requirement_text", "") if active_clauses else query
        sufficiency, missing_items, uncertainty = EvidenceSufficiencyClassifier.assess_sufficiency(
            clause_text=primary_req_text,
            evidence_items=sanitized_evidence,
            extracted_values=extracted_values,
            has_conflicts=bool(conflicts),
        )
        all_missing.extend(missing_items)

        # 7. Aggregate Candidate Assessment
        if conflicts:
            agg_candidate = CandidateAssessment.CONFLICTING_EVIDENCE
        elif sufficiency == EvidenceSufficiency.INSUFFICIENT or sufficiency == EvidenceSufficiency.UNVERIFIED:
            agg_candidate = CandidateAssessment.INSUFFICIENT_EVIDENCE
        elif any(c.candidate_assessment == CandidateAssessment.FAIL_CANDIDATE for c in candidates):
            agg_candidate = CandidateAssessment.FAIL_CANDIDATE
        elif candidates and all(c.candidate_assessment == CandidateAssessment.PASS_CANDIDATE for c in candidates):
            agg_candidate = CandidateAssessment.PASS_CANDIDATE
        else:
            agg_candidate = CandidateAssessment.NOT_ANALYZABLE

        # 8. Synthesize Technical Observations & Non-Authoritative Explanation
        observations: List[str] = []
        if candidates:
            for c in candidates:
                observations.append(
                    f"Clause {c.clause_number}: Evidence parameter {c.parameter_name} ({c.evidence_value} {c.evidence_unit}) "
                    f"compared against threshold ({c.required_operator} {c.required_value} {c.required_unit}) -> Candidate: {c.candidate_assessment.value}."
                )
        if conflicts:
            for conf in conflicts:
                observations.append(f"Discrepancy: {conf.discrepancy_explanation}")

        explanation = (
            f"Evidence Analysis for standard {target_standard}: "
            f"Analyzed {len(active_clauses)} requirements across {len(sanitized_evidence)} evidence items. "
            f"Sufficiency: {sufficiency.value}. "
            f"Candidate Assessment: {agg_candidate.value}. "
            f"Final compliance determination is deferred to Layer 7 Compliance Gap Engine."
        )

        return StructuredAnalysisResult(
            standard_number=target_standard,
            requirements_analyzed_count=len(active_clauses),
            evidence_items_analyzed_count=len(sanitized_evidence),
            requirement_matches=matches,
            extracted_values=extracted_values,
            comparison_candidates=candidates,
            evidence_sufficiency=sufficiency,
            evidence_conflicts=conflicts,
            missing_evidence=all_missing,
            technical_observations=observations,
            candidate_assessment=agg_candidate,
            uncertainty_state=uncertainty,
            analysis_explanation=explanation,
            sanitized_prompt_injections=all_injections,
            authority="AI_DERIVED / CANDIDATE",
            regulatory_conclusion="NONE",
            llm_compliance_authority=0.0,
        )

    def _normalize_unit_safe(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        tool_executor: Optional[Any] = None,
    ) -> Tuple[float, str]:
        """Performs unit conversion with deterministic deduplication and caching."""
        cache_key = f"norm:{value}:{from_unit}->{to_unit}"
        if cache_key in self.tool_cache:
            self.metrics["cache_hits"] += 1
            self.metrics["duplicate_calls_prevented"] += 1
            return self.tool_cache[cache_key]

        # Short-circuit if units identical
        if from_unit.strip().lower() == to_unit.strip().lower():
            self.metrics["short_circuits"] += 1
            return value, to_unit

        res_val, res_unit = deterministic_normalize_unit(float(value), from_unit, to_unit)
        self.metrics["tool_calls"] += 1
        self.tool_cache[cache_key] = (res_val, res_unit)
        return res_val, res_unit


# Global Singleton Instance
analysis_agent = AnalysisAgent()
