"""Layer 2 Product DNA Lifecycle & Versioning Service.

Coordinates:
- Fact extraction & normalization
- Clarification queue management
- User confirmation & correction with immutable audit trails
- Versioned Product DNA snapshots (v1.0, v1.1, etc.)
- Handoff of validated Product DNA to Layer 3 AI Orchestrator.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.schemas.product_dna import (
    ProductFact,
    FactProvenanceType,
    FactVerificationState,
    FactAuditEntry,
    ClarificationRequirement,
    ProductDNAVersionRecord,
    ProductDNACore,
)
from backend.app.services.product_dna.extractor import (
    extract_structured_facts_from_payload,
    extract_product_dna_from_text,
)
from backend.app.services.product_dna.detector import fact_anomaly_detector

# In-memory store for versioned Product DNA records
DNA_SNAPSHOT_REGISTRY: Dict[str, List[ProductDNAVersionRecord]] = {}


class ProductDNAService:
    """Manages versioned Product DNA facts and clarification workflows."""

    @classmethod
    def create_initial_dna(
        cls,
        dna_id: str,
        text: str,
        source_name: Optional[str] = None,
        default_provenance: FactProvenanceType = FactProvenanceType.USER_CLAIM,
        bom_components: Optional[List[Dict[str, Any]]] = None,
    ) -> ProductDNAVersionRecord:
        """Process multi-modal inputs and produce initial v1.0 Product DNA snapshot."""
        facts, prod_name, cat, sub_cat, intended_use = extract_structured_facts_from_payload(
            text=text,
            source_name=source_name,
            default_provenance=default_provenance,
            bom_components=bom_components,
        )

        clarifications = fact_anomaly_detector.identify_missing_discriminators(
            product_name=prod_name,
            category=cat,
            facts=facts,
        )

        completeness = cls.calculate_fact_completeness(facts, clarifications)

        snapshot = ProductDNAVersionRecord(
            dna_id=dna_id,
            version="v1.0",
            created_at=datetime.utcnow(),
            product_name=prod_name,
            category=cat,
            sub_category=sub_cat,
            intended_use=intended_use,
            facts=facts,
            clarification_queue=clarifications,
            fact_completeness_percentage=completeness,
            is_ready_for_orchestrator=len(clarifications) == 0 and completeness >= 70.0,
        )

        DNA_SNAPSHOT_REGISTRY[dna_id] = [snapshot]
        return snapshot

    @classmethod
    def get_latest_dna(cls, dna_id: str) -> Optional[ProductDNAVersionRecord]:
        """Fetch the most recent Product DNA version."""
        history = DNA_SNAPSHOT_REGISTRY.get(dna_id, [])
        return history[-1] if history else None

    @classmethod
    def confirm_fact(cls, dna_id: str, fact_id: str) -> ProductDNAVersionRecord:
        """Mark a fact as confirmed by the user."""
        current = cls.get_latest_dna(dna_id)
        if not current:
            raise ValueError(f"Product DNA '{dna_id}' not found.")

        updated_facts = []
        for f in current.facts:
            f_copy = f.model_copy(deep=True)
            if f_copy.fact_id == fact_id:
                f_copy.verification_state = FactVerificationState.CONFIRMED
            updated_facts.append(f_copy)

        return cls._create_next_version(current, updated_facts, current.clarification_queue)

    @classmethod
    def correct_fact(
        cls,
        dna_id: str,
        fact_id: str,
        new_value: Any,
        reason: str = "User specification correction",
    ) -> ProductDNAVersionRecord:
        """Allow user to correct an extracted fact, preserving original value and audit trail."""
        current = cls.get_latest_dna(dna_id)
        if not current:
            raise ValueError(f"Product DNA '{dna_id}' not found.")

        updated_facts = []
        for f in current.facts:
            f_copy = f.model_copy(deep=True)
            if f_copy.fact_id == fact_id:
                # Add to history
                audit = FactAuditEntry(
                    timestamp=datetime.utcnow(),
                    old_value=f_copy.value,
                    new_value=new_value,
                    reason=reason,
                    updated_by="user",
                )
                f_copy.history.append(audit)
                f_copy.value = new_value
                f_copy.verification_state = FactVerificationState.USER_CORRECTED
                f_copy.provenance = FactProvenanceType.USER_CLARIFICATION
            updated_facts.append(f_copy)

        return cls._create_next_version(current, updated_facts, current.clarification_queue)

    @classmethod
    def answer_clarification(
        cls,
        dna_id: str,
        attribute_name: str,
        value: Any,
    ) -> ProductDNAVersionRecord:
        """Resolve a blocking clarification requirement with explicit USER_CLARIFICATION provenance."""
        current = cls.get_latest_dna(dna_id)
        if not current:
            raise ValueError(f"Product DNA '{dna_id}' not found.")

        # Remove answered requirement from queue
        remaining_reqs = [r for r in current.clarification_queue if r.attribute_name != attribute_name]

        # Add or update corresponding fact
        updated_facts = [f.model_copy(deep=True) for f in current.facts]
        existing_fact = next((f for f in updated_facts if f.field_name == attribute_name), None)


        if existing_fact:
            existing_fact.value = value
            existing_fact.provenance = FactProvenanceType.USER_CLARIFICATION
            existing_fact.verification_state = FactVerificationState.CONFIRMED
        else:
            updated_facts.append(
                ProductFact(
                    fact_id=f"FACT-CLARIFY-{len(updated_facts)+1}",
                    field_name=attribute_name,
                    display_name=attribute_name.replace("_", " ").title(),
                    value=value,
                    raw_value=str(value),
                    source="User Clarification Queue",
                    provenance=FactProvenanceType.USER_CLARIFICATION,
                    confidence=1.0,
                    verification_state=FactVerificationState.CONFIRMED,
                )
            )

        return cls._create_next_version(current, updated_facts, remaining_reqs)

    @classmethod
    def calculate_fact_completeness(
        cls,
        facts: List[ProductFact],
        clarifications: List[ClarificationRequirement],
    ) -> float:
        """Compute Fact Completeness percentage (0.0 to 100.0). NEVER implies compliance."""
        if not facts and not clarifications:
            return 0.0

        # Confirmed or user-corrected facts carry full score, unconfirmed carry partial
        score = sum(1.0 if f.verification_state in (FactVerificationState.CONFIRMED, FactVerificationState.USER_CORRECTED) else 0.7 for f in facts)
        total_possible = len(facts) + (len(clarifications) * 1.5)

        pct = round((score / max(total_possible, 1.0)) * 100.0, 1)
        return min(100.0, pct)

    @classmethod
    def _create_next_version(
        cls,
        current: ProductDNAVersionRecord,
        facts: List[ProductFact],
        clarifications: List[ClarificationRequirement],
    ) -> ProductDNAVersionRecord:
        """Generate incremented immutable version (e.g. v1.0 -> v1.1)."""
        curr_ver_num = float(current.version.replace("v", ""))
        next_ver = f"v{curr_ver_num + 0.1:.1f}"

        completeness = cls.calculate_fact_completeness(facts, clarifications)

        new_record = ProductDNAVersionRecord(
            dna_id=current.dna_id,
            version=next_ver,
            created_at=datetime.utcnow(),
            product_name=current.product_name,
            category=current.category,
            sub_category=current.sub_category,
            intended_use=current.intended_use,
            facts=facts,
            clarification_queue=clarifications,
            fact_completeness_percentage=completeness,
            is_ready_for_orchestrator=len(clarifications) == 0 and completeness >= 70.0,
        )

        DNA_SNAPSHOT_REGISTRY.setdefault(current.dna_id, []).append(new_record)
        return new_record


product_dna_service = ProductDNAService()
