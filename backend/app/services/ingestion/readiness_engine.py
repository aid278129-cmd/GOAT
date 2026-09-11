"""Dynamic Document Readiness & Input Completeness Engine.

Evaluates multi-modal input completeness against verified BIS/QCO knowledge.
Clearly separates REQUIRED, OPTIONAL, and MISSING information.
Strict Invariant:
Readiness reflects INPUT COMPLETENESS only and NEVER implies regulatory compliance.
USER TEXT != EVIDENCE != COMPLIANCE.
"""

import re
from typing import Dict, Any, List, Optional
from backend.app.schemas.unified_input import (
    FieldRequirementLevel,
    FieldReadinessStatus,
    ReadinessFieldEvaluation,
    ReadinessChecklist,
    InputProvenanceType,
)
from backend.app.services.ingestion.template_generator import template_generator_service


class DocumentReadinessEngine:
    """Computes dynamic checklist and readiness score for Layer 1 inputs."""

    @classmethod
    def evaluate_readiness(
        cls,
        product_name: str,
        category: str,
        description: str,
        target_standard: Optional[str] = None,
        provenance_type: InputProvenanceType = InputProvenanceType.USER_CLAIM,
    ) -> ReadinessChecklist:
        """Evaluate input completeness against verified BIS requirements."""
        reqs = template_generator_service.get_requirements_for_standard_or_category(
            target_standard=target_standard,
            category=category,
        )

        clean_desc = (description or "").lower()
        clean_name = (product_name or "").strip()

        evaluations: List[ReadinessFieldEvaluation] = []
        required_count = 0
        present_required = 0
        optional_count = 0
        present_optional = 0
        missing_critical: List[str] = []

        for req in reqs:
            is_present = False
            extracted_val = None

            if req.level == FieldRequirementLevel.REQUIRED:
                required_count += 1
            elif req.level == FieldRequirementLevel.OPTIONAL:
                optional_count += 1

            # Check presence
            if req.field_id == "product_trade_name":
                if clean_name and len(clean_name) > 2:
                    is_present = True
                    extracted_val = clean_name
            elif req.field_id == "rated_voltage":
                m = re.search(r"(\d+(?:\.\d+)?)\s*(?:v\b|volt)", clean_desc)
                if m:
                    is_present = True
                    extracted_val = f"{m.group(1)} V AC"
            elif req.field_id == "rated_power_input":
                m = re.search(r"(\d+(?:\.\d+)?)\s*(?:w\b|watt|kw)", clean_desc)
                if m:
                    is_present = True
                    extracted_val = f"{m.group(1)} W"
            elif req.field_id == "rated_frequency":
                m = re.search(r"(\d+)\s*(?:hz|hertz)", clean_desc)
                if m:
                    is_present = True
                    extracted_val = f"{m.group(1)} Hz"
            elif req.field_id in ("heating_element_material", "inner_lining_material"):
                for alloy in ["stainless steel", "copper", "ss 304", "ss 316", "aluminum", "brass"]:
                    if alloy in clean_desc:
                        is_present = True
                        extracted_val = alloy.title()
                        break
            elif req.field_id in ("handle_material", "lid_seal_polymer"):
                for mat in ["polypropylene", "polymer", "silicone", "plastic", "bakelite", "rubber"]:
                    if mat in clean_desc:
                        is_present = True
                        extracted_val = mat.title()
                        break
            elif req.field_id == "power_cord_type":
                if any(w in clean_desc for w in ["cord", "pvc", "cable", "flexible"]):
                    is_present = True
                    extracted_val = "PVC Insulated Cord"
            elif req.field_id == "plug_top_rating":
                if any(w in clean_desc for w in ["plug", "3-pin", "pin", "6a", "16a"]):
                    is_present = True
                    extracted_val = "3-Pin Molded Plug"
            elif req.field_id == "nominal_capacity":
                m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|liter|litre|l\b)", clean_desc)
                if m:
                    is_present = True
                    extracted_val = f"{m.group(1)}"
            elif req.field_id == "heat_retention_spec":
                if any(w in clean_desc for w in ["heat retention", "temperature", "thermal", "65"]):
                    is_present = True
                    extracted_val = "Thermal retention declared"
            elif req.field_id == "lab_test_report_number":
                m = re.search(r"(?:report|ref|certificate)\s*#?\s*([a-z0-9\-_/]+)", clean_desc)
                if m:
                    is_present = True
                    extracted_val = m.group(1)

            # Record status
            if is_present:
                status = FieldReadinessStatus.SATISFIED
                if req.level == FieldRequirementLevel.REQUIRED:
                    present_required += 1
                else:
                    present_optional += 1
            else:
                if req.level == FieldRequirementLevel.REQUIRED:
                    status = FieldReadinessStatus.MISSING
                    missing_critical.append(req.field_name)
                elif req.level == FieldRequirementLevel.UNKNOWN:
                    status = FieldReadinessStatus.UNKNOWN
                else:
                    status = FieldReadinessStatus.MISSING

            evaluations.append(
                ReadinessFieldEvaluation(
                    field_id=req.field_id,
                    field_name=req.field_name,
                    level=req.level,
                    status=status,
                    extracted_value=extracted_val,
                    provenance=provenance_type if is_present else None,
                    action_required=None if is_present else f"Provide '{req.field_name}' in specifications or BOM.",
                )
            )

        # Calculate completeness percentage (0 to 100%)
        # Required fields carry 85% weight, optional carry 15%
        required_weight = (present_required / max(required_count, 1)) * 85.0
        optional_weight = (present_optional / max(optional_count, 1)) * 15.0 if optional_count > 0 else 15.0
        total_percentage = round(min(100.0, required_weight + optional_weight), 1)

        is_ready = present_required >= required_count and required_count > 0

        return ReadinessChecklist(
            total_required_fields=required_count,
            present_required_fields=present_required,
            missing_required_fields=required_count - present_required,
            optional_fields_count=optional_count,
            present_optional_fields=present_optional,
            completeness_percentage=total_percentage,
            evaluations=evaluations,
            missing_critical_fields=missing_critical,
            is_ready_for_dna_compilation=is_ready,
        )


document_readiness_engine = DocumentReadinessEngine()
