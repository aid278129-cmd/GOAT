/**
 * GOAT Universal Evidence Ingestion Domain Types & Constants.
 * 
 * Enforces the Cardinal Regulatory Rule:
 * File Processing != Evidence Acceptance != Engineering Assessment != Human Attestation != BIS Certification
 */

export const EvidenceCategory = {
  PDF: 'PDF',
  AUDIO: 'AUDIO',
  IMAGE: 'IMAGE',
  ENGINEERING: 'ENGINEERING',
};

export const EvidenceSubType = {
  // PDF Document Subtypes
  BIS_STANDARD: { id: 'BIS_STANDARD', label: 'Official BIS Standard', category: EvidenceCategory.PDF, icon: 'menu_book' },
  LAB_TEST_REPORT: { id: 'LAB_TEST_REPORT', label: 'Laboratory Test Report', category: EvidenceCategory.PDF, icon: 'science' },
  CERTIFICATE: { id: 'CERTIFICATE', label: 'Test / Safety Certificate', category: EvidenceCategory.PDF, icon: 'verified' },
  DATASHEET: { id: 'DATASHEET', label: 'Component / Technical Datasheet', category: EvidenceCategory.PDF, icon: 'description' },
  DECLARATION: { id: 'DECLARATION', label: 'Manufacturer Declaration', category: EvidenceCategory.PDF, icon: 'fact_check' },
  TECHNICAL_DOC: { id: 'TECHNICAL_DOC', label: 'Technical Construction File', category: EvidenceCategory.PDF, icon: 'article' },

  // Audio Recording Subtypes
  ENGINEER_INTERVIEW: { id: 'ENGINEER_INTERVIEW', label: 'Engineer Interview / Inspection', category: EvidenceCategory.AUDIO, icon: 'mic' },
  LAB_DISCUSSION: { id: 'LAB_DISCUSSION', label: 'Laboratory Technical Discussion', category: EvidenceCategory.AUDIO, icon: 'record_voice_over' },
  VOICE_NOTE: { id: 'VOICE_NOTE', label: 'Acoustic Voice Note', category: EvidenceCategory.AUDIO, icon: 'graphic_eq' },
  INSPECTION_OBSERVATION: { id: 'INSPECTION_OBSERVATION', label: 'Live Inspection Observation', category: EvidenceCategory.AUDIO, icon: 'hearing' },

  // Visual Image Subtypes
  PRODUCT_PHOTO: { id: 'PRODUCT_PHOTO', label: 'Product Physical Photograph', category: EvidenceCategory.IMAGE, icon: 'photo_camera' },
  NAMEPLATE: { id: 'NAMEPLATE', label: 'Statutory Rating Nameplate', category: EvidenceCategory.IMAGE, icon: 'badge' },
  LABEL: { id: 'LABEL', label: 'BIS Standard Marking & Label', category: EvidenceCategory.IMAGE, icon: 'sell' },
  PCB_PHOTO: { id: 'PCB_PHOTO', label: 'PCB Layout / Assembly Photo', category: EvidenceCategory.IMAGE, icon: 'memory' },
  INSPECTION_PHOTO: { id: 'INSPECTION_PHOTO', label: 'Disassembly / Creepage Inspection', category: EvidenceCategory.IMAGE, icon: 'zoom_in' },

  // Engineering & CAD Subtypes
  STEP_CAD: { id: 'STEP_CAD', label: 'STEP / STP 3D CAD Geometry', category: EvidenceCategory.ENGINEERING, icon: 'view_in_ar' },
  GERBER: { id: 'GERBER', label: 'Gerber PCB Production Layer', category: EvidenceCategory.ENGINEERING, icon: 'layers' },
  BOM: { id: 'BOM', label: 'Bill of Materials (BOM / CSV)', category: EvidenceCategory.ENGINEERING, icon: 'table_view' },
  SCHEMATIC: { id: 'SCHEMATIC', label: 'Electrical Circuit Schematic', category: EvidenceCategory.ENGINEERING, icon: 'account_tree' },
};

export const ProcessingStatus = {
  UPLOADED: 'UPLOADED',
  QUEUED: 'QUEUED',
  PROCESSING: 'PROCESSING',
  EXTRACTION_COMPLETE: 'EXTRACTION_COMPLETE',
};

export const AcceptanceStatus = {
  PENDING_REVIEW: 'PENDING_REVIEW',
  REQUIRES_REVIEW: 'REQUIRES_REVIEW',
  ACCEPTED: 'ACCEPTED',
  REJECTED: 'REJECTED',
};

export const EngineeringAssessmentStatus = {
  NOT_EVALUATED: 'NOT_EVALUATED',
  NON_CONFORMANT: 'NON_CONFORMANT',
  CONFORMANT: 'CONFORMANT',
  INFORMATION_REQUIRED: 'INFORMATION_REQUIRED',
};

export const HumanAttestationStatus = {
  UNSIGNED: 'UNSIGNED',
  SIGNED: 'SIGNED',
};

export const BisCertificationStatus = {
  NOT_SUBMITTED: 'NOT_SUBMITTED',
  SUBMITTED: 'SUBMITTED',
  CERTIFIED: 'CERTIFIED',
};

export const ArtifactIntegrityStatus = {
  CALCULATING: 'CALCULATING',
  HASH_VALID: 'HASH_VALID',
  HASH_MISMATCH: 'HASH_MISMATCH',
};
