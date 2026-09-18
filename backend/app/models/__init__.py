from backend.app.models.base import Base
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence, EvidenceLifecycleEvent
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_assessment import AssessmentRun, PersistentAssessmentResult, ComplianceFinding
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.persistent_review import ReviewItem, HumanAttestation
from backend.app.models.persistent_cad import (
    CADModel,
    CADComponent,
    CADGeometryFeature,
    CADMeasurement,
    CADSnapshot,
    CADProcessingStatus,
)

# Retain legacy/reference models
from backend.app.models.product import Product
from backend.app.models.product_attribute import ProductAttribute
from backend.app.models.source import Source
from backend.app.models.document import Document
from backend.app.models.standard import Standard
from backend.app.models.clause import Clause
from backend.app.models.requirement import Requirement
from backend.app.models.amendment import Amendment
from backend.app.models.regulatory_instrument import RegulatoryInstrument
from backend.app.models.verification_record import VerificationRecord
from backend.app.models.test import StandardTest
from backend.app.models.evidence import Evidence
from backend.app.models.requirement_evidence_link import RequirementEvidenceLink
from backend.app.models.compliance_result import ComplianceResult
from backend.app.models.decision_record import DecisionRecord
from backend.app.models.laboratory import Laboratory
from backend.app.models.persistent_ai import (
    AIConversation,
    AIMessage,
    AIExecution,
    AIToolCall,
    AIActionProposal,
)
from backend.app.models.conversation import Conversation
from backend.app.models.assessment import Assessment, AssessmentSnapshot, AssessmentStatus

__all__ = [
    "Base",
    "Organization",
    "User",
    "ComplianceJob",
    "PersistentEvidence",
    "EvidenceLifecycleEvent",
    "PersistentDNA",
    "JobStandard",
    "JobRequirement",
    "AssessmentRun",
    "PersistentAssessmentResult",
    "ComplianceFinding",
    "AuditEvent",
    "ReviewItem",
    "HumanAttestation",
    "CADModel",
    "CADComponent",
    "CADGeometryFeature",
    "CADMeasurement",
    "CADSnapshot",
    "CADProcessingStatus",
    "AIConversation",
    "AIMessage",
    "AIExecution",
    "AIToolCall",
    "AIActionProposal",
    "Product",
    "ProductAttribute",
    "Source",
    "Document",
    "Standard",
    "Clause",
    "Requirement",
    "Amendment",
    "RegulatoryInstrument",
    "VerificationRecord",
    "StandardTest",
    "Evidence",
    "RequirementEvidenceLink",
    "ComplianceResult",
    "DecisionRecord",
    "Laboratory",
    "Conversation",
    "Assessment",
    "AssessmentSnapshot",
    "AssessmentStatus",
]
