"""Regulatory Claim Grounding Schemas (Milestone M25.2A).

Enforces Cardinal Non-Negotiables:
1. Every regulatory claim must be traceable to:
   source -> document -> standard -> revision -> clause -> requirement.
2. A claim is rejected if:
   - source is missing
   - source is unverified
   - source authenticity is unknown or untrusted
   - clause is missing where clause-level support is required
3. LLM / ML authority = 0.0%.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from backend.app.schemas.product_evidence import SourceAuthenticity, EvidenceVerificationStatus


class ClaimType(str, Enum):
    """Classification of regulatory compliance claim."""
    APPLICABILITY_MANDATE = "APPLICABILITY_MANDATE"
    STANDARD_VERSION_SCOPE = "STANDARD_VERSION_SCOPE"
    CLAUSE_CONFORMANCE = "CLAUSE_CONFORMANCE"
    TEST_METHOD_REQUIREMENT = "TEST_METHOD_REQUIREMENT"
    MARKING_REQUIREMENT = "MARKING_REQUIREMENT"
    EXEMPTION_ASSERTION = "EXEMPTION_ASSERTION"


class ClaimGroundingStatus(str, Enum):
    """Validation state of a regulatory claim."""
    FULLY_GROUNDED = "FULLY_GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    UNGROUNDED = "UNGROUNDED"
    REJECTED = "REJECTED"


class RegulatoryClaimRecord(BaseModel):
    """A strictly grounded, auditable regulatory claim anchored to an authoritative source."""
    claim_id: str = Field(..., description="Unique claim identifier e.g. CLAIM-IS302-CL13")
    claim_type: ClaimType = Field(..., description="Type of regulatory assertion")
    claim_text: str = Field(..., description="Verbatim or canonical claim statement")
    standard_number: str = Field(..., description="Governing BIS standard e.g. IS 302-2-21")
    standard_revision: str = Field(..., description="Specific active edition e.g. 2011 (Consolidated)")
    clause_number: str = Field(..., description="Mandatory clause citation e.g. Clause 13.2")
    requirement_id: str = Field(..., description="Linked requirement ID")
    source_id: str = Field(..., description="Document or gazette source identifier")
    source_hash: str = Field(..., description="SHA-256 digest of the source document")
    source_authenticity: SourceAuthenticity = Field(
        default=SourceAuthenticity.UNVERIFIED,
        description="Authenticity classification of the source document",
    )
    verification_status: EvidenceVerificationStatus = Field(
        default=EvidenceVerificationStatus.UNVERIFIED,
        description="Source verification status",
    )
    authority_level: str = Field(
        default="GAZETTED_MANDATE",
        description="Statutory level e.g. GAZETTED_MANDATE, DPIIT_QCO, VOLUNTARY_STANDARD",
    )
    grounding_status: ClaimGroundingStatus = Field(
        default=ClaimGroundingStatus.UNGROUNDED,
        description="Deterministic grounding status",
    )
    rejection_reason: Optional[str] = Field(None, description="Reason if claim is rejected")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)

    def validate_claim(self) -> bool:
        """Evaluate deterministic grounding of this regulatory claim.
        
        Strict Invariants:
        Reject claim if:
        1. Source missing or empty.
        2. Source hash missing or invalid length.
        3. Source authenticity is UNVERIFIED, REJECTED, or ACQUISITION_PENDING.
        4. Verification status is not VERIFIED.
        5. Clause number is missing or empty when clause support is required.
        """
        if not self.source_id or not self.source_id.strip():
            self.grounding_status = ClaimGroundingStatus.REJECTED
            self.rejection_reason = "Source document ID is missing."
            return False

        if not self.source_hash or len(self.source_hash) != 64:
            self.grounding_status = ClaimGroundingStatus.REJECTED
            self.rejection_reason = "Source document hash is missing or invalid SHA-256."
            return False

        if self.source_authenticity in (
            SourceAuthenticity.UNVERIFIED,
            SourceAuthenticity.REJECTED,
            SourceAuthenticity.ACQUISITION_PENDING,
        ):
            self.grounding_status = ClaimGroundingStatus.REJECTED
            self.rejection_reason = f"Source authenticity is {self.source_authenticity.value}; ungrounded claim."
            return False

        if self.verification_status != EvidenceVerificationStatus.VERIFIED:
            self.grounding_status = ClaimGroundingStatus.REJECTED
            self.rejection_reason = f"Source verification status is {self.verification_status.value}; must be VERIFIED."
            return False

        if not self.clause_number or self.clause_number.strip() in ("", "N/A", "UNKNOWN"):
            self.grounding_status = ClaimGroundingStatus.REJECTED
            self.rejection_reason = "Specific clause citation is required but missing."
            return False

        self.grounding_status = ClaimGroundingStatus.FULLY_GROUNDED
        self.rejection_reason = None
        return True
