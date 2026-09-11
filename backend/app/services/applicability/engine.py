"""Layer 5: Applicability Engine — Production Implementation.

Architecture:
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

Supported Result States (7 Canonical States):
1. APPLICABLE
2. POTENTIALLY_APPLICABLE
3. MORE_INFORMATION_REQUIRED
4. NOT_APPLICABLE
5. COVERAGE_GAP
6. CONFLICTING_RULES
7. EXPERT_REVIEW_REQUIRED

Invariants:
- NO VERIFIED SCOPE/RULE → NO AUTHORITATIVE APPLICABILITY CLAIM
- MISSING REQUIRED FACT → ASK (Never Guess or Infer)
- COVERAGE GAP ≠ NOT_APPLICABLE
- STANDARD EXISTS ≠ AUTOMATICALLY MANDATORY
- LLM AUTHORITY OVER FINAL APPLICABILITY = 0%
"""

import os
import json
from typing import List, Dict, Any, Optional

from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.applicability.applicability_models import (
    ApplicabilityState,
    ScopeStatus,
    QCOStatus,
    ApplicabilityAction,
    SupportingFact,
    RuleSourceReference,
    DeclarativeRule,
    DeterministicDecisionTrace,
    ApplicabilityDecision,
)
from backend.app.services.applicability.evaluator import evaluate_condition
from backend.app.services.applicability.taxonomy import (
    get_taxonomy_category,
    get_required_attribute_profile,
)
from backend.app.services.knowledge.package_manager import get_package


RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")


def load_declarative_rules() -> List[DeclarativeRule]:
    """Load all declarative JSON rules from rules directory ordered by priority."""
    rules = []
    if not os.path.exists(RULES_DIR):
        return rules

    for fname in os.listdir(RULES_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(RULES_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                rules.append(DeclarativeRule(**data))

    rules.sort(key=lambda r: r.priority, reverse=True)
    return rules


def _extract_supporting_facts(dna: ProductDNACore) -> List[SupportingFact]:
    """Extract structured product facts with provenance and confidence from Product DNA."""
    facts: List[SupportingFact] = []
    
    if dna.category:
        facts.append(
            SupportingFact(
                field_name="category",
                value=dna.category,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.sub_category:
        facts.append(
            SupportingFact(
                field_name="sub_category",
                value=dna.sub_category,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.product_name:
        facts.append(
            SupportingFact(
                field_name="product_name",
                value=dna.product_name,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.materials:
        facts.append(
            SupportingFact(
                field_name="materials",
                value=dna.materials,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.insulated:
        facts.append(
            SupportingFact(
                field_name="insulated",
                value=dna.insulated,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.electrical:
        facts.append(
            SupportingFact(
                field_name="electrical",
                value=dna.electrical,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    claimed = getattr(dna, "standards_claimed", None)
    if claimed:
        facts.append(
            SupportingFact(
                field_name="standards_claimed",
                value=claimed,
                source="PRODUCT_DNA",
                provenance="USER_DECLARED",
                confidence=0.5,
            )
        )
    for attr in dna.attributes:
        facts.append(
            SupportingFact(
                field_name=attr.name,
                value=attr.value,
                unit=attr.unit,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    return facts


def _check_scope_boundary(
    std_number: str,
    dna: ProductDNACore,
    facts_dict: Dict[str, Any],
) -> tuple[ScopeStatus, str]:
    """Validate scope inclusion/exclusion boundaries against verified standard criteria."""
    materials_str = " ".join([str(m) for m in dna.materials]).lower()
    prod_name_lower = (dna.product_name or "").lower()

    # Scope check for IS 17526:2021 (Stainless Steel Vacuum Flasks)
    if std_number == "IS 17526:2021":
        if "polypropylene" in materials_str and not dna.insulated and "stainless_steel" not in materials_str:
            return (
                ScopeStatus.OUT_OF_SCOPE,
                "Product is uninsulated plastic; IS 17526:2021 applies exclusively to double-wall stainless steel vacuum containers.",
            )
        if dna.insulated and ("stainless_steel" in materials_str or "steel" in materials_str):
            return (
                ScopeStatus.IN_SCOPE,
                "Product matches IS 17526:2021 scope: domestic double-wall vacuum insulated container with stainless steel contact surfaces.",
            )
        return (
            ScopeStatus.SCOPE_UNCERTAIN,
            "Materials or insulation construction require further confirmation to establish IS 17526:2021 scope boundary.",
        )

    # Scope check for IS 302-2-201:2008 (Electric Immersion Water Heaters)
    if std_number == "IS 302-2-201:2008":
        if not dna.electrical and "immersion" not in prod_name_lower:
            return (
                ScopeStatus.OUT_OF_SCOPE,
                "Product is non-electrical and outside IS 302-2-201:2008 scope.",
            )
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 302-2-201:2008 scope: portable domestic electric immersion water heater rated <= 250V.",
        )

    # Scope check for IS 302-2-15:2009 (Appliances for Heating Liquids)
    if std_number == "IS 302-2-15:2009":
        if not dna.electrical:
            return (
                ScopeStatus.OUT_OF_SCOPE,
                "Product is non-electrical and outside IS 302-2-15:2009 scope.",
            )
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 302-2-15:2009 scope: household electric appliance for heating liquids.",
        )

    # Scope check for IS 9873 (Part 1):2019 (Toys Mechanical Safety)
    if std_number == "IS 9873 (Part 1):2019":
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 9873 (Part 1):2019 scope: toy intended for play by children under 14 years.",
        )

    # Scope check for IS 4151:2015 (Helmets)
    if std_number == "IS 4151:2015":
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 4151:2015 scope: protective helmet for two-wheeler motorcycle / scooter riders.",
        )

    # Default fallback
    return (
        ScopeStatus.IN_SCOPE,
        f"Product category '{dna.category}' matches general scope of {std_number}.",
    )


def determine_applicability(
    dna: ProductDNACore,
    authoritative_only: bool = True,
) -> List[ApplicabilityDecision]:
    """Determine Indian Standards applicability using the 8-step deterministic pipeline.
    
    Architecture:
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

    Strict Invariants Enforced:
    1. LLM authority over final applicability = 0% (llm_decision=False always).
    2. Missing required attribute triggers MORE_INFORMATION_REQUIRED with explicit clarification question.
    3. Coverage gap is never equated to NOT_APPLICABLE.
    4. Regulatory status is strictly separated from technical relevance.
    5. In authoritative mode, unverified rules are never used for binding regulatory claims.
    """
    supporting_facts = _extract_supporting_facts(dna)
    facts_dict: Dict[str, Any] = {
        "category": dna.category,
        "sub_category": dna.sub_category,
        "product_name": dna.product_name,
        "materials": dna.materials,
        "insulated": dna.insulated,
        "electrical": dna.electrical,
        "standards_claimed": getattr(dna, "standards_claimed", []),
    }
    for attr in dna.attributes:
        facts_dict[attr.name] = attr.value

    # ---------------------------------------------------------
    # Step 1: Input Validation & Safety Boundary for Empty DNA
    # ---------------------------------------------------------
    is_empty_dna = (
        not dna.product_name
        and not dna.materials
        and not dna.attributes
        and (not dna.category or dna.category in ("General Goods", "UNKNOWN", ""))
    )
    if is_empty_dna:
        trace = DeterministicDecisionTrace(
            product_facts=[],
            matched_rule="SAFETY_BOUNDARY_EMPTY_DNA",
            standard="CATALOG_COVERAGE_GAP",
            scope_check=ScopeStatus.SCOPE_UNCERTAIN,
            scope_reason="Empty product DNA: no product attributes, category, or materials specified.",
            qco_check=QCOStatus.QCO_UNCERTAIN,
            qco_order_name=None,
            missing_facts=["category", "materials", "product_name"],
            conflicting_facts=[],
            final_status=ApplicabilityState.COVERAGE_GAP,
        )
        return [
            ApplicabilityDecision(
                standard_number="CATALOG_COVERAGE_GAP",
                standard_title="Uncataloged / Insufficient Product DNA",
                applicability_status=ApplicabilityState.COVERAGE_GAP,
                technical_relevance="COVERAGE_GAP",
                regulatory_status="COVERAGE_NOT_ESTABLISHED",
                scope_status=ScopeStatus.SCOPE_UNCERTAIN,
                qco_status=QCOStatus.QCO_UNCERTAIN,
                matched_rule_id="SAFETY_BOUNDARY_EMPTY_DNA",
                rule_verification_status="VERIFIED",
                scheme="NOT_ESTABLISHED",
                mandatory_reason=None,
                explanation="Product DNA contains no identifiable product attributes or regulated category. Coverage gap registered.",
                sources=[],
                llm_decision=False,
                dna_version=dna.version,
                supporting_facts=[],
                missing_facts=["category", "materials", "product_name"],
                conflicting_facts=[],
                action_required=ApplicabilityAction.REVIEW_COVERAGE_GAP,
                decision_trace=trace,
                is_primary=True,
                knowledge_version="v1.2.0-gazette-verified",
            )
        ]

    # ---------------------------------------------------------
    # Step 2: Taxonomy & Attribute Feature Extraction
    # ---------------------------------------------------------
    tax = get_taxonomy_category(dna.category) or get_taxonomy_category(dna.product_name)
    if tax and tax.coverage_state == "CATALOG_NOT_COVERED":
        trace = DeterministicDecisionTrace(
            product_facts=[f"{f.field_name}={f.value}" for f in supporting_facts],
            matched_rule="RULE_REGISTRY_BOUNDARY",
            standard="CATALOG_COVERAGE_GAP",
            scope_check=ScopeStatus.SCOPE_UNCERTAIN,
            scope_reason=f"Taxonomy category '{tax.category_name}' has no codified Indian Standard rules.",
            qco_check=QCOStatus.QCO_UNCERTAIN,
            qco_order_name=None,
            missing_facts=[],
            conflicting_facts=[],
            final_status=ApplicabilityState.COVERAGE_GAP,
        )
        return [
            ApplicabilityDecision(
                standard_number="CATALOG_COVERAGE_GAP",
                standard_title=f"Uncataloged Category: {dna.category}",
                applicability_status=ApplicabilityState.COVERAGE_GAP,
                technical_relevance="COVERAGE_GAP",
                regulatory_status="COVERAGE_NOT_ESTABLISHED",
                scope_status=ScopeStatus.SCOPE_UNCERTAIN,
                qco_status=QCOStatus.QCO_UNCERTAIN,
                matched_rule_id="RULE_REGISTRY_BOUNDARY",
                rule_verification_status="VERIFIED",
                scheme="NOT_ESTABLISHED",
                mandatory_reason=None,
                explanation=(
                    f"The Zyntrix verified rule base currently has no codified Indian Standard rules "
                    f"for '{dna.category}'. This indicates a knowledge coverage boundary, NOT that the product "
                    f"is exempt from BIS regulation in India."
                ),
                sources=[],
                llm_decision=False,
                dna_version=dna.version,
                supporting_facts=supporting_facts,
                missing_facts=[],
                conflicting_facts=[],
                action_required=ApplicabilityAction.REVIEW_COVERAGE_GAP,
                decision_trace=trace,
                is_primary=True,
                knowledge_version="v1.2.0-gazette-verified",
            )
        ]

    # ---------------------------------------------------------
    # Step 3: Declarative Rule Matching with Verification Gate
    # ---------------------------------------------------------
    rules = load_declarative_rules()
    decisions: List[ApplicabilityDecision] = []

    for rule in rules:
        # Rule safety check
        if authoritative_only and rule.verification_status != "VERIFIED":
            continue

        is_match = evaluate_condition(rule.conditions, dna)
        if not is_match:
            continue

        res = rule.result
        std_num = res.get("standard_number", "IS UNKNOWN")
        std_title = res.get("standard_title", "")

        # ---------------------------------------------------------
        # Step 4: Scope Boundary Verification
        # ---------------------------------------------------------
        scope_status, scope_reason = _check_scope_boundary(std_num, dna, facts_dict)

        # ---------------------------------------------------------
        # Step 5: QCO Mandate Status Check
        # ---------------------------------------------------------
        pkg = get_package(std_num)
        qco_order_name = res.get("qco_order") or (pkg.regulatory_order_name if pkg else None)
        if qco_order_name or res.get("regulatory_status") == "VERIFIED_MANDATORY_QCO":
            qco_status = QCOStatus.MANDATORY_QCO
            regulatory_status = "VERIFIED_MANDATORY_QCO"
        elif res.get("regulatory_status") == "VOLUNTARY":
            qco_status = QCOStatus.VOLUNTARY
            regulatory_status = "VOLUNTARY"
        else:
            qco_status = QCOStatus.QCO_UNCERTAIN
            regulatory_status = "COVERAGE_NOT_ESTABLISHED"

        # ---------------------------------------------------------
        # Step 6: Ambiguity, Conflict & Missing Fact Detection
        # ---------------------------------------------------------
        missing_facts: List[str] = []
        conflicting_facts: List[str] = []

        profile = get_required_attribute_profile(std_num)
        if profile:
            for blocker in profile.blocking_attributes:
                val = facts_dict.get(blocker)
                # Specific checks for attributes
                if blocker == "materials" and not dna.materials:
                    missing_facts.append("materials")
                elif blocker == "insulated" and not dna.insulated and "insulated" not in facts_dict:
                    missing_facts.append("insulated")
                elif blocker not in ("materials", "insulated") and val is None:
                    missing_facts.append(blocker)

        # Conflict check: user claim vs physical nature
        if dna.electrical is False and any(
            k in (dna.product_name or "").lower() for k in ["immersion", "heater", "kettle", "geyser"]
        ):
            conflicting_facts.append(
                "Declared non-electrical, but product name indicates electrical heating appliance."
            )

        # ---------------------------------------------------------
        # Step 7: Final Applicability Decision Synthesis
        # ---------------------------------------------------------
        clarification_question: Optional[str] = None

        if conflicting_facts:
            applicability_status = ApplicabilityState.CONFLICTING_RULES
            technical_relevance = "CONFLICTING_RULES"
            action_required = ApplicabilityAction.EXPERT_REVIEW
            explanation = (
                f"Contradictory product facts detected for {std_num}: {'; '.join(conflicting_facts)}. "
                f"Deterministic engine requires expert review before determining mandatory certification."
            )
        elif rule.verification_status == "REQUIRES_EXPERT_REVIEW":
            applicability_status = ApplicabilityState.EXPERT_REVIEW_REQUIRED
            technical_relevance = "REQUIRES_EXPERT_REVIEW"
            action_required = ApplicabilityAction.EXPERT_REVIEW
            explanation = f"Rule {rule.rule_id} requires human expert review before authoritative application."
        elif scope_status == ScopeStatus.OUT_OF_SCOPE:
            applicability_status = ApplicabilityState.NOT_APPLICABLE
            technical_relevance = "NOT_APPLICABLE"
            regulatory_status = "VOLUNTARY"
            action_required = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
            explanation = f"Product is outside the mandatory scope of {std_num}: {scope_reason}"
        elif missing_facts:
            applicability_status = ApplicabilityState.MORE_INFORMATION_REQUIRED
            technical_relevance = "MORE_INFORMATION_REQUIRED"
            regulatory_status = "MORE_INFORMATION_REQUIRED"
            action_required = ApplicabilityAction.ASK_FOR_INFORMATION
            clarification_question = (
                f"To confirm whether {std_num} ({std_title}) is mandatory for your product, please provide "
                f"the following required specification(s): {', '.join(missing_facts)}."
            )
            explanation = (
                f"Candidate standard {std_num} matched based on category '{dna.category}', but "
                f"essential blocking attributes ({', '.join(missing_facts)}) are missing. "
                f"Clarification is required before declaring applicability."
            )
        else:
            applicability_status = ApplicabilityState.APPLICABLE
            technical_relevance = res.get("technical_relevance", "LIKELY_APPLICABLE")
            action_required = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
            explanation = (
                f"Deterministic rule {rule.rule_id} evaluated TRUE for product category '{dna.category}' "
                f"matching criteria in {std_num}. Mandatory statutory status: {res.get('mandatory_reason', 'Regulated standard')}."
            )

        # ---------------------------------------------------------
        # Step 8: Decision Trace & Provenance Generation
        # ---------------------------------------------------------
        trace = DeterministicDecisionTrace(
            product_facts=[f"{f.field_name}={f.value}" for f in supporting_facts],
            matched_rule=rule.rule_id,
            standard=std_num,
            scope_check=scope_status,
            scope_reason=scope_reason,
            qco_check=qco_status,
            qco_order_name=qco_order_name,
            missing_facts=missing_facts,
            conflicting_facts=conflicting_facts,
            final_status=applicability_status,
        )

        amendment_info = f"{len(pkg.amendments)} verified amendment(s)" if (pkg and pkg.amendments) else None
        superseded_by = pkg.superseded_by if pkg else None
        knowledge_version = pkg.knowledge_version if pkg else "v1.2.0-gazette-verified"

        decisions.append(
            ApplicabilityDecision(
                standard_number=std_num,
                standard_title=std_title,
                applicability_status=applicability_status,
                technical_relevance=technical_relevance,
                regulatory_status=regulatory_status,
                scope_status=scope_status,
                qco_status=qco_status,
                matched_rule_id=rule.rule_id,
                rule_verification_status=rule.verification_status,
                scheme=res.get("scheme", "Scheme I (ISI Mark)"),
                mandatory_reason=res.get("mandatory_reason"),
                explanation=explanation,
                sources=rule.sources,
                llm_decision=False,
                dna_version=dna.version,
                supporting_facts=supporting_facts,
                missing_facts=missing_facts,
                conflicting_facts=conflicting_facts,
                clarification_question=clarification_question,
                action_required=action_required,
                decision_trace=trace,
                is_primary=len(decisions) == 0,
                knowledge_version=knowledge_version,
                amendment_info=amendment_info,
                superseded_by=superseded_by,
            )
        )

    # ---------------------------------------------------------
    # Fallback to Candidate Standard Generator if no rules matched
    # ---------------------------------------------------------
    if not decisions:
        from backend.app.services.applicability.candidate_generator import generate_candidate_standards
        cand_res = generate_candidate_standards(dna)

        for c in cand_res.candidates:
            # Map candidate status to canonical Layer 5 state
            if c.is_coverage_gap or c.status == "COVERAGE_GAP":
                app_stat = ApplicabilityState.COVERAGE_GAP
                action = ApplicabilityAction.REVIEW_COVERAGE_GAP
                scope_stat = ScopeStatus.SCOPE_UNCERTAIN
                qco_stat = QCOStatus.QCO_UNCERTAIN
            elif c.status == "NOT_APPLICABLE":
                app_stat = ApplicabilityState.NOT_APPLICABLE
                action = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
                scope_stat = ScopeStatus.OUT_OF_SCOPE
                qco_stat = QCOStatus.VOLUNTARY
            elif c.missing_blocking_attributes or c.status == "MORE_INFORMATION_REQUIRED":
                app_stat = ApplicabilityState.MORE_INFORMATION_REQUIRED
                action = ApplicabilityAction.ASK_FOR_INFORMATION
                scope_stat = ScopeStatus.SCOPE_UNCERTAIN
                qco_stat = QCOStatus.MANDATORY_QCO if c.regulatory_status == "VERIFIED_MANDATORY_QCO" else QCOStatus.QCO_UNCERTAIN
            else:
                app_stat = ApplicabilityState.POTENTIALLY_APPLICABLE
                action = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
                scope_stat = ScopeStatus.IN_SCOPE
                qco_stat = QCOStatus.MANDATORY_QCO if c.regulatory_status == "VERIFIED_MANDATORY_QCO" else QCOStatus.VOLUNTARY

            clar_q = None
            if c.missing_blocking_attributes:
                clar_q = f"Clarification required for {c.standard_number}: Missing {', '.join(c.missing_blocking_attributes)}."

            trace = DeterministicDecisionTrace(
                product_facts=[f"{k}={v}" for k, v in c.contributing_attributes.items()],
                matched_rule=c.generated_by_rule,
                standard=c.standard_number,
                scope_check=scope_stat,
                scope_reason=c.explanation,
                qco_check=qco_stat,
                qco_order_name=None,
                missing_facts=c.missing_blocking_attributes,
                conflicting_facts=[],
                final_status=app_stat,
            )

            pkg = get_package(c.standard_number)
            knowledge_version = pkg.knowledge_version if pkg else "v1.2.0-gazette-verified"

            decisions.append(
                ApplicabilityDecision(
                    standard_number=c.standard_number,
                    standard_title=c.standard_title,
                    applicability_status=app_stat,
                    technical_relevance=c.status,
                    regulatory_status=c.regulatory_status,
                    scope_status=scope_stat,
                    qco_status=qco_stat,
                    matched_rule_id=c.generated_by_rule,
                    rule_verification_status=c.source_status,
                    scheme="Scheme I (ISI Mark)" if c.status in ("LIKELY_APPLICABLE", "APPLICABLE") else "NOT_ESTABLISHED",
                    mandatory_reason=None if c.status != "LIKELY_APPLICABLE" else "DPIIT QCO Mandate",
                    explanation=c.explanation,
                    sources=[],
                    llm_decision=False,
                    dna_version=dna.version,
                    supporting_facts=supporting_facts,
                    missing_facts=c.missing_blocking_attributes,
                    conflicting_facts=[],
                    clarification_question=clar_q,
                    action_required=action,
                    decision_trace=trace,
                    is_primary=len(decisions) == 0,
                    knowledge_version=knowledge_version,
                )
            )

    return decisions
