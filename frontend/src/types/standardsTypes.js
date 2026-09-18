/**
 * Zyntrix Regulatory Compliance Engineering Workstation
 * Stage 03 — Standards & Clause Intelligence Types & Schemas
 *
 * REGULATORY MANDATE:
 * Evaluator outputs are strictly classified under ENGINEERING ASSESSMENT.
 * They must never be presented as BIS Certification, BIS Approval,
 * Laboratory Certification, or Statutory Attestation.
 */

// Deterministic Comparison Rule Operators
export const ComparisonType = {
  GREATER_THAN: 'GREATER_THAN',
  GREATER_THAN_OR_EQUAL: 'GREATER_THAN_OR_EQUAL',
  LESS_THAN: 'LESS_THAN',
  LESS_THAN_OR_EQUAL: 'LESS_THAN_OR_EQUAL',
  EQUAL: 'EQUAL',
  RANGE: 'RANGE',
  ENUMERATION: 'ENUMERATION',
  BOOLEAN: 'BOOLEAN',
  TEXT_REVIEW: 'TEXT_REVIEW',
  NOT_APPLICABLE: 'NOT_APPLICABLE',
};

export const COMPARISON_TYPE_LABELS = {
  [ComparisonType.GREATER_THAN]: 'Greater Than (>)',
  [ComparisonType.GREATER_THAN_OR_EQUAL]: 'Greater Than or Equal (≥)',
  [ComparisonType.LESS_THAN]: 'Less Than (<)',
  [ComparisonType.LESS_THAN_OR_EQUAL]: 'Less Than or Equal (≤)',
  [ComparisonType.EQUAL]: 'Exact Match (==)',
  [ComparisonType.RANGE]: 'Numerical Tolerance Range [Min - Max]',
  [ComparisonType.ENUMERATION]: 'Enumerated Set Membership (One of)',
  [ComparisonType.BOOLEAN]: 'Boolean Statutory Condition (True / False)',
  [ComparisonType.TEXT_REVIEW]: 'Descriptive Engineering Review',
  [ComparisonType.NOT_APPLICABLE]: 'Not Applicable by Scope (N/A)',
};

// Requirement Domain Classification
export const RequirementType = {
  ELECTRICAL: 'ELECTRICAL',
  SAFETY: 'SAFETY',
  MECHANICAL: 'MECHANICAL',
  ENVIRONMENTAL: 'ENVIRONMENTAL',
  MATERIALS: 'MATERIALS',
  MARKING_LABELS: 'MARKING_LABELS',
  COMPONENTS: 'COMPONENTS',
  INTERFACES: 'INTERFACES',
};

export const REQUIREMENT_TYPE_LABELS = {
  [RequirementType.ELECTRICAL]: 'Electrical Safety & Ratings',
  [RequirementType.SAFETY]: 'Protection Against Electric Shock & Hazards',
  [RequirementType.MECHANICAL]: 'Physical Enclosure & Mechanical Strength',
  [RequirementType.ENVIRONMENTAL]: 'Environmental Envelope & Thermal Stress',
  [RequirementType.MATERIALS]: 'Polymer Flammability & Tracking Resistance',
  [RequirementType.MARKING_LABELS]: 'Statutory Markings, Nameplates & Symbols',
  [RequirementType.COMPONENTS]: 'Critical Component Construction & Ratings',
  [RequirementType.INTERFACES]: 'Supply Connection & External Terminations',
};

// Regulatory Verification Method
export const VerificationMethod = {
  TYPE_TEST: 'TYPE_TEST',
  VISUAL_INSPECTION: 'VISUAL_INSPECTION',
  DOCUMENTATION_REVIEW: 'DOCUMENTATION_REVIEW',
  CALCULATION: 'CALCULATION',
  ROUTINE_TEST: 'ROUTINE_TEST',
};

export const VERIFICATION_METHOD_LABELS = {
  [VerificationMethod.TYPE_TEST]: 'Laboratory Type Testing',
  [VerificationMethod.VISUAL_INSPECTION]: 'Physical / Visual Inspection',
  [VerificationMethod.DOCUMENTATION_REVIEW]: 'Technical File & Certificate Audit',
  [VerificationMethod.CALCULATION]: 'Engineering Calculation / Simulation',
  [VerificationMethod.ROUTINE_TEST]: 'Factory Production Routine Verification',
};

// Traceability Match State between Requirement and Product DNA
// Invariant: None of these states may be called PASS or COMPLIANT.
export const ProductDnaMatchState = {
  NO_MATCHING_DNA: 'NO_MATCHING_DNA',
  DNA_AVAILABLE: 'DNA_AVAILABLE',
  EVIDENCE_BACKED_DNA: 'EVIDENCE_BACKED_DNA',
  CONFLICTING_DNA: 'CONFLICTING_DNA',
  READY_FOR_ASSESSMENT: 'READY_FOR_ASSESSMENT',
};

export const DNA_MATCH_CONFIG = {
  [ProductDnaMatchState.NO_MATCHING_DNA]: {
    label: 'No Matching Product DNA',
    bg: 'bg-slate-100 text-slate-700 border-slate-300',
    icon: 'help_outline',
    description: 'Parameter is not present in Product DNA facts repository.',
  },
  [ProductDnaMatchState.DNA_AVAILABLE]: {
    label: 'Product DNA Available (Unverified)',
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: 'info',
    description: 'Parameter exists in Product DNA but is not marked verified.',
  },
  [ProductDnaMatchState.EVIDENCE_BACKED_DNA]: {
    label: 'Evidence-Backed Product DNA',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: 'verified',
    description: 'Parameter verified and anchored to accepted evidence artifact.',
  },
  [ProductDnaMatchState.CONFLICTING_DNA]: {
    label: 'Conflicting Product DNA',
    bg: 'bg-amber-50 text-amber-700 border-amber-300',
    icon: 'warning',
    description: 'Parameter has active unresolved conflicting evidence artifacts.',
  },
  [ProductDnaMatchState.READY_FOR_ASSESSMENT]: {
    label: 'Ready for Engineering Assessment',
    bg: 'bg-purple-50 text-purple-700 border-purple-200',
    icon: 'rule',
    description: 'Verified parameter backed by accepted evidence ready for deterministic evaluation.',
  },
};

// Explicit Engineering Assessment Output States
// STRICT MANDATE: Clearly labeled ENGINEERING ASSESSMENT and never presented as BIS/Lab certification.
export const EngineeringAssessmentState = {
  NOT_ASSESSED: 'NOT_ASSESSED',
  DATA_REQUIRED: 'DATA_REQUIRED',
  CONFLICT: 'CONFLICT',
  NOT_APPLICABLE: 'NOT_APPLICABLE',
  ENGINEERING_PASS: 'ENGINEERING_PASS',
  ENGINEERING_GAP: 'ENGINEERING_GAP',
  HUMAN_REVIEW_REQUIRED: 'HUMAN_REVIEW_REQUIRED',
};

export const ASSESSMENT_STATE_CONFIG = {
  [EngineeringAssessmentState.NOT_ASSESSED]: {
    label: 'Not Assessed',
    badge: 'bg-slate-100 text-slate-700 border-slate-300',
    icon: 'pending',
    explanation: 'Deterministic evaluation rule has not been executed.',
  },
  [EngineeringAssessmentState.DATA_REQUIRED]: {
    label: 'Data Required (Missing DNA)',
    badge: 'bg-amber-50 text-amber-800 border-amber-300',
    icon: 'hourglass_empty',
    explanation: 'Assessment blocked: Required parameter missing from verified Product DNA.',
  },
  [EngineeringAssessmentState.CONFLICT]: {
    label: 'Parameter Conflict (Unresolved)',
    badge: 'bg-red-50 text-red-800 border-red-300',
    icon: 'error_outline',
    explanation: 'Assessment blocked: Underlying Product DNA parameter has an active unresolved evidence conflict.',
  },
  [EngineeringAssessmentState.NOT_APPLICABLE]: {
    label: 'Not Applicable by Scope',
    badge: 'bg-slate-100 text-slate-600 border-slate-300',
    icon: 'block',
    explanation: 'Clause requirement is outside current product operational envelope or scope.',
  },
  [EngineeringAssessmentState.ENGINEERING_PASS]: {
    label: 'Engineering Conformance: PASS',
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    icon: 'check_circle',
    explanation: 'Deterministic rule satisfied by verified Product DNA backed by accepted evidence.',
  },
  [EngineeringAssessmentState.ENGINEERING_GAP]: {
    label: 'Engineering Gap Identified',
    badge: 'bg-rose-50 text-rose-800 border-rose-300',
    icon: 'cancel',
    explanation: 'Product DNA value fails to satisfy numerical or statutory threshold rule.',
  },
  [EngineeringAssessmentState.HUMAN_REVIEW_REQUIRED]: {
    label: 'Human Engineering Review Required',
    badge: 'bg-indigo-50 text-indigo-800 border-indigo-300',
    icon: 'rate_review',
    explanation: 'Qualitative statutory clause requires human engineer interpretation and sign-off.',
  },
};
