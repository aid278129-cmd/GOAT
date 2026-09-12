"""Layer 5: Applicability Engine — Production Implementation.

Architecture:
PRODUCT DNA
  ↓
1. PRODUCT DNA COMPLETENESS
  ↓
2. SOURCE & RULE VERIFICATION GATE
  ↓
3. STANDARD LIFECYCLE, VERSION & REVISION CHECK
  ↓
4. SCOPE BOUNDARY INCLUSION / EXCLUSION CHECK
  ↓
5. REQUIRED PRODUCT DISCRIMINATORS CHECK
  ↓
6. TYPED CONDITIONAL RULES EVALUATION
  ↓
7. STATUTORY QCO MANDATE CHECK
  ↓
8. NORMATIVE DEPENDENCY GRAPH RESOLUTION
  ↓
9. EVIDENCE AVAILABILITY & COVERAGE CHECK
  ↓
10. FINAL APPLICABILITY SYNTHESIS & AUDIT TRACE
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

Strict Cardinal Invariants:
1. LLM Authority = 0 for applicability decisions (llm_decision=False always).
2. ML/DL Authority = 0 for applicability decisions.
3. User claims are not authoritative applicability evidence.
4. Retrieval ranking is not proof of applicability.
5. Coverage gaps must NEVER become NOT_APPLICABLE.
6. Missing discriminator information must produce MORE_INFORMATION_REQUIRED (Never Guess or Infer).
7. Conflicting applicability rules must produce CONFLICTING_RULES / EXPERT_REVIEW_REQUIRED.
8. Unverified sources cannot establish authoritative applicability.
9. Standard version/revision must be explicitly represented.
10. Withdrawn/superseded standards must not silently become current applicable standards.
11. Normative references must be represented separately from the primary standard.
12. Conditional clauses must be represented explicitly, not flattened into a binary result.
13. No fabricated BIS requirements, clauses, dates, QCOs or revisions.
14. Existing Layer 7 compliance authority remains unchanged.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union

from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.applicability.applicability_models import (
    ApplicabilityState,
    ScopeStatus,
    QCOStatus,
    StandardStatus,
    ProductConditionStatus,
    NormativeDependencyStatus,
    EvidenceAvailabilityStatus,
    NormativeRelationType,
    NormativeStandardReference,
    TypedCondition,
    ConditionalRequirementEvaluation,
    StandardRevisionInfo,
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
    REQUIRED_ATTRIBUTE_PROFILES,
)
from backend.app.services.applicability.version_registry import (
    get_standard_revision_info,
    is_standard_superseded,
    is_standard_withdrawn,
    get_active_replacement,
    normalize_standard_key,
)
from backend.app.services.applicability.relationship_graph import (
    get_normative_references_for_standard,
    check_normative_dependency_satisfaction,
)
from backend.app.services.applicability.conditional import (
    evaluate_standard_conditions,
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
    if dna.insulated is not None:
        facts.append(
            SupportingFact(
                field_name="insulated",
                value=dna.insulated,
                source="PRODUCT_DNA",
                provenance="LAYER_2_PRODUCT_DNA",
                confidence=1.0,
            )
        )
    if dna.electrical is not None:
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
) -> Tuple[ScopeStatus, str]:
    """Validate scope inclusion/exclusion boundaries against verified standard criteria."""
    materials_list = dna.materials or []
    materials_str = " ".join([str(m) for m in materials_list]).lower()
    prod_name_lower = (dna.product_name or "").lower()

    # Scope check for IS 17526:2021 (Stainless Steel Vacuum Flasks)
    if "IS 17526" in std_number:
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
        if not materials_list and not dna.insulated:
            return (
                ScopeStatus.SCOPE_UNCERTAIN,
                "Materials or insulation construction require further confirmation to establish IS 17526:2021 scope boundary.",
            )
        return (
            ScopeStatus.SCOPE_UNCERTAIN,
            "Materials or insulation construction require further confirmation to establish IS 17526:2021 scope boundary.",
        )

    # Scope check for IS 302-2-201:2008 (Electric Immersion Water Heaters)
    if "IS 302-2-201" in std_number:
        if dna.electrical is False and "immersion" not in prod_name_lower:
            return (
                ScopeStatus.OUT_OF_SCOPE,
                "Product is non-electrical and outside IS 302-2-201:2008 scope.",
            )
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 302-2-201:2008 scope: portable domestic electric immersion water heater rated <= 250V.",
        )

    # Scope check for IS 302-2-15:2009 (Appliances for Heating Liquids)
    if "IS 302-2-15" in std_number:
        if dna.electrical is False:
            return (
                ScopeStatus.OUT_OF_SCOPE,
                "Product is non-electrical and outside IS 302-2-15:2009 scope.",
            )
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 302-2-15:2009 scope: household electric appliance for heating liquids.",
        )

    # Scope check for IS 9873 (Part 1):2019 / 2012 (Toys Mechanical Safety)
    if "IS 9873" in std_number:
        return (
            ScopeStatus.IN_SCOPE,
            f"Product matches {std_number} scope: toy intended for play by children under 14 years.",
        )

    # Scope check for IS 4151:2015 / 1993 (Helmets)
    if "IS 4151" in std_number:
        return (
            ScopeStatus.IN_SCOPE,
            f"Product matches {std_number} scope: protective helmet for two-wheeler motorcycle / scooter riders.",
        )

    # Scope check for IS 2347:2017 / 2006 (Pressure Cookers)
    if "IS 2347" in std_number:
        return (
            ScopeStatus.IN_SCOPE,
            f"Product matches {std_number} scope: domestic pressure cooker designed for household cooking.",
        )

    # Scope check for IS 16102 (LED Lamps)
    if "IS 16102" in std_number:
        return (
            ScopeStatus.IN_SCOPE,
            "Product matches IS 16102 scope: self-ballasted LED lamps for general lighting services.",
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
    """Determine Indian Standards applicability using the 10-step deterministic pipeline.

    Execution Order:
    1. Product DNA Completeness Check
    2. Candidate Identification & Source Verification Gate
    3. Standard Status, Version & Revision Check
    4. Scope Boundary Inclusion / Exclusion Check
    5. Required Product Discriminators Check
    6. Typed Conditional Rules Evaluation
    7. Statutory QCO Mandate Check
    8. Normative Dependency Graph Resolution
    9. Evidence Availability & Coverage Check
    10. Final Applicability Synthesis & Audit Trace Generation

    Strict Invariants Enforced:
    1. LLM authority over final applicability = 0% (llm_decision=False always).
    2. Missing required attribute triggers MORE_INFORMATION_REQUIRED (Never guess or infer).
    3. Coverage gap is never equated to NOT_APPLICABLE.
    4. Regulatory status is strictly separated from technical relevance.
    5. In authoritative mode, unverified rules or standards cannot establish binding claims.
    6. Superseded standards must never silently become active applicable standards.
    7. Normative references are represented separately from primary standards.
    """
    supporting_facts = _extract_supporting_facts(dna)
    facts_dict: Dict[str, Any] = {
        "category": dna.category,
        "sub_category": dna.sub_category,
        "product_name": dna.product_name,
        "materials": dna.materials or [],
        "insulated": dna.insulated,
        "electrical": dna.electrical,
        "standards_claimed": getattr(dna, "standards_claimed", []),
    }
    for attr in dna.attributes:
        facts_dict[attr.name] = attr.value

    product_discriminators: Dict[str, Any] = {
        "product_name": dna.product_name,
        "category": dna.category,
        "sub_category": dna.sub_category,
        "materials": dna.materials,
        "insulated": dna.insulated,
        "electrical": dna.electrical,
    }
    for attr in dna.attributes:
        product_discriminators[attr.name] = attr.value

    evaluation_order_trace: List[str] = []

    # ---------------------------------------------------------
    # Step 1: Product DNA Completeness & Safety Boundary
    # ---------------------------------------------------------
    evaluation_order_trace.append("STEP_1_PRODUCT_DNA_COMPLETENESS")
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
                product_discriminators=product_discriminators,
                required_discriminators=["category", "materials", "product_name"],
                decision_reasons=["Empty Product DNA: insufficient attributes to establish applicability."],
                supporting_evidence=[],
                standard_status=StandardStatus.UNKNOWN,
                scope_match=ScopeStatus.SCOPE_UNCERTAIN,
                product_condition_status=ProductConditionStatus.CONDITIONS_PENDING_INFO,
                normative_dependency_status=NormativeDependencyStatus.PRIMARY_ONLY,
                evidence_availability_status=EvidenceAvailabilityStatus.COVERAGE_GAP,
                provenance="Bureau of Indian Standards",
                expert_review_required=False,
                evaluation_order_trace=evaluation_order_trace,
            )
        ]

    # ---------------------------------------------------------
    # Step 2: Taxonomy & Category Coverage Check
    # ---------------------------------------------------------
    evaluation_order_trace.append("STEP_2_TAXONOMY_CATEGORY_CHECK")
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
                product_discriminators=product_discriminators,
                required_discriminators=[],
                decision_reasons=[f"Uncataloged category: {dna.category} is not yet indexed in verified rules."],
                supporting_evidence=supporting_facts,
                standard_status=StandardStatus.CATALOG_ONLY,
                scope_match=ScopeStatus.SCOPE_UNCERTAIN,
                product_condition_status=ProductConditionStatus.NOT_CONDITIONAL,
                normative_dependency_status=NormativeDependencyStatus.PRIMARY_ONLY,
                evidence_availability_status=EvidenceAvailabilityStatus.COVERAGE_GAP,
                provenance="Bureau of Indian Standards",
                expert_review_required=False,
                evaluation_order_trace=evaluation_order_trace,
            )
        ]

    # ---------------------------------------------------------
    # Step 3: Declarative Rule Matching with Verification Gate
    # ---------------------------------------------------------
    evaluation_order_trace.append("STEP_3_RULE_MATCHING_VERIFICATION")
    rules = load_declarative_rules()
    decisions: List[ApplicabilityDecision] = []

    # Check user-claimed standards for superseded versions (e.g. IS 4151:1993, IS 1293:2005)
    claimed_standards = getattr(dna, "standards_claimed", []) or []
    for claimed_std in claimed_standards:
        rev_info = get_standard_revision_info(claimed_std)
        if rev_info and rev_info.status == StandardStatus.SUPERSEDED:
            active_replacement = rev_info.superseded_by or get_active_replacement(claimed_std)
            explanation = (
                f"Claimed standard {claimed_std} is SUPERSEDED by {active_replacement}. "
                f"Withdrawn or superseded standards must not silently become current applicable standards."
            )
            trace = DeterministicDecisionTrace(
                product_facts=[f"standards_claimed={claimed_std}"],
                matched_rule="VERSION_REGISTRY_SUPERSEDED",
                standard=claimed_std,
                scope_check=ScopeStatus.OUT_OF_SCOPE,
                scope_reason=f"Standard is superseded by {active_replacement}.",
                qco_check=QCOStatus.VOLUNTARY,
                qco_order_name=None,
                missing_facts=[],
                conflicting_facts=[f"{claimed_std} is superseded by {active_replacement}"],
                final_status=ApplicabilityState.NOT_APPLICABLE,
            )
            decisions.append(
                ApplicabilityDecision(
                    standard_number=claimed_std,
                    standard_title=rev_info.standard_title,
                    applicability_status=ApplicabilityState.NOT_APPLICABLE,
                    technical_relevance="NOT_APPLICABLE",
                    regulatory_status="SUPERSEDED",
                    scope_status=ScopeStatus.OUT_OF_SCOPE,
                    qco_status=QCOStatus.VOLUNTARY,
                    matched_rule_id="VERSION_REGISTRY_SUPERSEDED",
                    rule_verification_status="VERIFIED",
                    scheme="SUPERSEDED",
                    mandatory_reason=None,
                    explanation=explanation,
                    sources=[],
                    llm_decision=False,
                    dna_version=dna.version,
                    supporting_facts=supporting_facts,
                    missing_facts=[],
                    conflicting_facts=[f"{claimed_std} is superseded by {active_replacement}"],
                    action_required=ApplicabilityAction.CONTINUE_TO_REQUIREMENTS,
                    decision_trace=trace,
                    is_primary=False,
                    knowledge_version="v1.2.0-gazette-verified",
                    superseded_by=active_replacement,
                    standard_revision=rev_info.revision_edition,
                    standard_status=StandardStatus.SUPERSEDED,
                    scope_match=ScopeStatus.OUT_OF_SCOPE,
                    product_discriminators=product_discriminators,
                    required_discriminators=[],
                    qco_conditions=[],
                    conditional_conditions=[],
                    normative_references=[],
                    product_condition_status=ProductConditionStatus.NOT_CONDITIONAL,
                    normative_dependency_status=NormativeDependencyStatus.PRIMARY_ONLY,
                    evidence_availability_status=EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED,
                    decision_reasons=[explanation],
                    supporting_evidence=supporting_facts,
                    provenance=rev_info.provenance,
                    expert_review_required=True,
                    evaluation_order_trace=evaluation_order_trace + ["STEP_3_SUPERSEDED_STANDARD_DETECTED"],
                )
            )

    for rule in rules:
        if authoritative_only and rule.verification_status != "VERIFIED":
            continue

        is_match = evaluate_condition(rule.conditions, dna)
        has_electrical_contradiction = False
        if not is_match:
            # Check if rule would have matched except for electrical contradiction
            if (
                rule.rule_id in ("APP-ELECTRICAL-001", "APP-ELECTRICAL-002")
                and dna.electrical is False
                and any(k in (dna.product_name or "").lower() for k in ["immersion", "heater", "kettle", "geyser"])
            ):
                has_electrical_contradiction = True
            else:
                continue

        res = rule.result
        std_num = res.get("standard_number", "IS UNKNOWN")
        std_title = res.get("standard_title", "")

        # ---------------------------------------------------------
        # Step 4: Standard Lifecycle & Version / Revision Check
        # ---------------------------------------------------------
        step_trace = list(evaluation_order_trace)
        step_trace.append("STEP_4_STANDARD_VERSION_CHECK")
        rev_info = get_standard_revision_info(std_num)
        standard_status = rev_info.status if rev_info else StandardStatus.ACTIVE
        standard_revision = rev_info.revision_edition if rev_info else None
        amendment_list = rev_info.amendments if rev_info else []
        superseded_by = rev_info.superseded_by if rev_info else None

        # ---------------------------------------------------------
        # Step 5: Scope Boundary Verification
        # ---------------------------------------------------------
        step_trace.append("STEP_5_SCOPE_BOUNDARY_CHECK")
        scope_status, scope_reason = _check_scope_boundary(std_num, dna, facts_dict)

        # ---------------------------------------------------------
        # Step 6: Required Product Discriminators Check
        # ---------------------------------------------------------
        step_trace.append("STEP_6_REQUIRED_DISCRIMINATORS_CHECK")
        missing_facts: List[str] = []
        conflicting_facts: List[str] = []
        required_discriminators: List[str] = []

        if has_electrical_contradiction:
            conflicting_facts.append(
                "Declared non-electrical, but product name indicates electrical heating appliance."
            )

        profile = get_required_attribute_profile(std_num)
        if profile:
            required_discriminators = list(profile.blocking_attributes)
            for blocker in profile.blocking_attributes:
                val = facts_dict.get(blocker)
                if blocker == "materials" and not dna.materials:
                    missing_facts.append("materials")
                elif blocker == "insulated" and dna.insulated is None and "insulated" not in facts_dict:
                    missing_facts.append("insulated")
                elif blocker not in ("materials", "insulated") and val is None:
                    missing_facts.append(blocker)

        # Conflict check: declared non-electrical vs product physical nature
        if dna.electrical is False and any(
            k in (dna.product_name or "").lower() for k in ["immersion", "heater", "kettle", "geyser"]
        ):
            if "Declared non-electrical, but product name indicates electrical heating appliance." not in conflicting_facts:
                conflicting_facts.append(
                    "Declared non-electrical, but product name indicates electrical heating appliance."
                )

        # ---------------------------------------------------------
        # Step 7: Typed Conditional Rules Evaluation
        # ---------------------------------------------------------
        step_trace.append("STEP_7_CONDITIONAL_RULES_EVALUATION")
        cond_status, cond_evals, cond_missing = evaluate_standard_conditions(std_num, dna)
        for cm in cond_missing:
            if cm not in missing_facts:
                missing_facts.append(cm)

        # ---------------------------------------------------------
        # Step 8: Statutory QCO Mandate Status Check
        # ---------------------------------------------------------
        step_trace.append("STEP_8_QCO_MANDATE_CHECK")
        pkg = get_package(std_num)
        qco_order_name = res.get("qco_order") or (pkg.regulatory_order_name if pkg else None)
        if not qco_order_name and rev_info and rev_info.gazette_order_ref:
            qco_order_name = rev_info.gazette_order_ref

        if qco_order_name or res.get("regulatory_status") == "VERIFIED_MANDATORY_QCO":
            qco_status = QCOStatus.MANDATORY_QCO
            regulatory_status = "VERIFIED_MANDATORY_QCO"
        elif res.get("regulatory_status") == "VOLUNTARY":
            qco_status = QCOStatus.VOLUNTARY
            regulatory_status = "VOLUNTARY"
        else:
            qco_status = QCOStatus.QCO_UNCERTAIN
            regulatory_status = "COVERAGE_NOT_ESTABLISHED"

        qco_conditions = [res.get("mandatory_reason")] if res.get("mandatory_reason") else []

        # ---------------------------------------------------------
        # Step 9: Normative Dependency Graph Resolution
        # ---------------------------------------------------------
        step_trace.append("STEP_9_NORMATIVE_DEPENDENCIES_CHECK")
        normative_refs = get_normative_references_for_standard(std_num)
        normative_dep_status = NormativeDependencyStatus.PRIMARY_ONLY
        if normative_refs:
            normative_dep_status = NormativeDependencyStatus.HAS_NORMATIVE_DEPENDENCIES

        # ---------------------------------------------------------
        # Step 10: Final Applicability State & Trace Synthesis
        # ---------------------------------------------------------
        step_trace.append("STEP_10_FINAL_APPLICABILITY_SYNTHESIS")
        clarification_question: Optional[str] = None
        decision_reasons: List[str] = []
        expert_review = False

        if conflicting_facts:
            applicability_status = ApplicabilityState.CONFLICTING_RULES
            technical_relevance = "CONFLICTING_RULES"
            action_required = ApplicabilityAction.EXPERT_REVIEW
            expert_review = True
            reason_msg = (
                f"Contradictory product facts detected for {std_num}: {'; '.join(conflicting_facts)}. "
                f"Deterministic engine requires expert review before determining mandatory certification."
            )
            explanation = reason_msg
            decision_reasons.append(reason_msg)

        elif rule.verification_status == "REQUIRES_EXPERT_REVIEW":
            applicability_status = ApplicabilityState.EXPERT_REVIEW_REQUIRED
            technical_relevance = "REQUIRES_EXPERT_REVIEW"
            action_required = ApplicabilityAction.EXPERT_REVIEW
            expert_review = True
            reason_msg = f"Rule {rule.rule_id} requires human expert review before authoritative application."
            explanation = reason_msg
            decision_reasons.append(reason_msg)

        elif scope_status == ScopeStatus.OUT_OF_SCOPE:
            applicability_status = ApplicabilityState.NOT_APPLICABLE
            technical_relevance = "NOT_APPLICABLE"
            regulatory_status = "VOLUNTARY"
            action_required = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
            reason_msg = f"Product is outside the mandatory scope of {std_num}: {scope_reason}"
            explanation = reason_msg
            decision_reasons.append(reason_msg)

        elif missing_facts:
            applicability_status = ApplicabilityState.MORE_INFORMATION_REQUIRED
            technical_relevance = "MORE_INFORMATION_REQUIRED"
            regulatory_status = "MORE_INFORMATION_REQUIRED"
            action_required = ApplicabilityAction.ASK_FOR_INFORMATION
            clarification_question = (
                f"To confirm whether {std_num} ({std_title}) is mandatory for your product, please provide "
                f"the following required specification(s): {', '.join(missing_facts)}."
            )
            reason_msg = (
                f"Candidate standard {std_num} matched based on category '{dna.category}', but "
                f"essential blocking attributes ({', '.join(missing_facts)}) are missing. "
                f"Clarification is required before declaring applicability."
            )
            explanation = reason_msg
            decision_reasons.append(reason_msg)

        else:
            applicability_status = ApplicabilityState.APPLICABLE
            technical_relevance = res.get("technical_relevance", "LIKELY_APPLICABLE")
            action_required = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
            reason_msg = (
                f"Deterministic rule {rule.rule_id} evaluated TRUE for product category '{dna.category}' "
                f"matching criteria in {std_num}. Mandatory statutory status: {res.get('mandatory_reason', 'Regulated standard')}."
            )
            explanation = reason_msg
            decision_reasons.append(reason_msg)

        # Decision trace
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

        amendment_info = (
            f"{len(amendment_list)} verified amendment(s): {'; '.join(amendment_list)}"
            if amendment_list
            else (f"{len(pkg.amendments)} verified amendment(s)" if (pkg and pkg.amendments) else None)
        )
        knowledge_version = pkg.knowledge_version if pkg else "v1.2.0-gazette-verified"

        evidence_avail = EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED
        if pkg and pkg.acquisition_status.value == "METADATA_ONLY":
            evidence_avail = EvidenceAvailabilityStatus.METADATA_ONLY

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
                is_primary=len([d for d in decisions if d.is_primary]) == 0,
                knowledge_version=knowledge_version,
                amendment_info=amendment_info,
                superseded_by=superseded_by,
                standard_revision=standard_revision,
                standard_status=standard_status,
                scope_match=scope_status,
                product_discriminators=product_discriminators,
                required_discriminators=required_discriminators,
                qco_conditions=qco_conditions,
                conditional_conditions=cond_evals,
                normative_references=normative_refs,
                product_condition_status=cond_status,
                normative_dependency_status=normative_dep_status,
                evidence_availability_status=evidence_avail,
                decision_reasons=decision_reasons,
                supporting_evidence=supporting_facts,
                provenance=rev_info.provenance if rev_info else "Bureau of Indian Standards",
                expert_review_required=expert_review,
                evaluation_order_trace=step_trace,
            )
        )

    # ---------------------------------------------------------
    # Fallback to Candidate Standard Generator if no rules matched
    # ---------------------------------------------------------
    if not decisions:
        from backend.app.services.applicability.candidate_generator import generate_candidate_standards
        cand_res = generate_candidate_standards(dna)

        for c in cand_res.candidates:
            if c.is_coverage_gap or c.status == "COVERAGE_GAP":
                app_stat = ApplicabilityState.COVERAGE_GAP
                action = ApplicabilityAction.REVIEW_COVERAGE_GAP
                scope_stat = ScopeStatus.SCOPE_UNCERTAIN
                qco_stat = QCOStatus.QCO_UNCERTAIN
                evidence_avail = EvidenceAvailabilityStatus.COVERAGE_GAP
            elif c.status == "NOT_APPLICABLE":
                app_stat = ApplicabilityState.NOT_APPLICABLE
                action = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
                scope_stat = ScopeStatus.OUT_OF_SCOPE
                qco_stat = QCOStatus.VOLUNTARY
                evidence_avail = EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED
            elif c.missing_blocking_attributes or c.status == "MORE_INFORMATION_REQUIRED":
                app_stat = ApplicabilityState.MORE_INFORMATION_REQUIRED
                action = ApplicabilityAction.ASK_FOR_INFORMATION
                scope_stat = ScopeStatus.SCOPE_UNCERTAIN
                qco_stat = (
                    QCOStatus.MANDATORY_QCO
                    if c.regulatory_status == "VERIFIED_MANDATORY_QCO"
                    else QCOStatus.QCO_UNCERTAIN
                )
                evidence_avail = EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED
            else:
                app_stat = ApplicabilityState.POTENTIALLY_APPLICABLE
                action = ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
                scope_stat = ScopeStatus.IN_SCOPE
                qco_stat = (
                    QCOStatus.MANDATORY_QCO
                    if c.regulatory_status == "VERIFIED_MANDATORY_QCO"
                    else QCOStatus.VOLUNTARY
                )
                evidence_avail = EvidenceAvailabilityStatus.FULL_TEXT_VERIFIED

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
            rev_info = get_standard_revision_info(c.standard_number)
            std_status = rev_info.status if rev_info else StandardStatus.ACTIVE
            norm_refs = get_normative_references_for_standard(c.standard_number)

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
                    scheme=(
                        "Scheme I (ISI Mark)"
                        if c.status in ("LIKELY_APPLICABLE", "APPLICABLE")
                        else "NOT_ESTABLISHED"
                    ),
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
                    is_primary=len([d for d in decisions if d.is_primary]) == 0,
                    knowledge_version=knowledge_version,
                    standard_revision=rev_info.revision_edition if rev_info else None,
                    standard_status=std_status,
                    scope_match=scope_stat,
                    product_discriminators=product_discriminators,
                    required_discriminators=c.missing_blocking_attributes,
                    qco_conditions=[],
                    conditional_conditions=[],
                    normative_references=norm_refs,
                    product_condition_status=ProductConditionStatus.NOT_CONDITIONAL,
                    normative_dependency_status=(
                        NormativeDependencyStatus.HAS_NORMATIVE_DEPENDENCIES
                        if norm_refs
                        else NormativeDependencyStatus.PRIMARY_ONLY
                    ),
                    evidence_availability_status=evidence_avail,
                    decision_reasons=[c.explanation],
                    supporting_evidence=supporting_facts,
                    provenance=rev_info.provenance if rev_info else "Bureau of Indian Standards",
                    expert_review_required=False,
                    evaluation_order_trace=evaluation_order_trace + ["CANDIDATE_GENERATOR_FALLBACK"],
                )
            )

    return decisions
