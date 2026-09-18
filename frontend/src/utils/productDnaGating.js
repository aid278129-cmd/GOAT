import { AcceptanceStatus } from '../types/evidenceTypes';
import { ParameterReviewStatus } from '../types/productDnaTypes';
import { formatTimestamp } from './evidenceCrypto';

/**
 * Strict Regulatory Evidence Gate.
 * Enforces: ONLY artifacts with Evidence Acceptance = ACCEPTED can contribute to Product DNA.
 */
export function isEvidenceEligibleForProductDNA(evidence) {
  if (!evidence) return false;
  return evidence.acceptanceStatus === AcceptanceStatus.ACCEPTED;
}

/**
 * Apply parameter extraction from an Accepted Evidence artifact into Product DNA.
 * Evaluates existing values for conflicts. If two accepted artifacts report different values,
 * does NOT pick automatically—flags a human resolution requirement.
 */
export function processParameterExtraction({
  existingFacts,
  conflicts,
  auditLog,
  evidence,
  parameterId,
  parameterName,
  section,
  extractedValue,
  unit,
  location,
  extractionMethod,
  confidence = 1.0,
  actor = 'Designated Regulatory Engineer',
}) {
  if (!isEvidenceEligibleForProductDNA(evidence)) {
    throw new Error(
      `Evidence Gating Violation: Artifact ${evidence?.id || 'UNKNOWN'} has status '${
        evidence?.acceptanceStatus || 'UNREVIEWED'
      }'. Only ACCEPTED evidence may populate Product DNA.`
    );
  }

  const timestamp = formatTimestamp();
  const existingFact = existingFacts[parameterId];

  // Case 1: No previous value exists -> Populate directly with provenance
  if (!existingFact || existingFact.value === null || existingFact.value === undefined || existingFact.value === '') {
    const newFact = {
      id: parameterId,
      section,
      name: parameterName,
      value: extractedValue,
      unit: unit || existingFact?.defaultUnit || '',
      sourceEvidenceId: evidence.id,
      sourceFileName: evidence.fileName,
      sourceLocation: location || 'Direct extraction',
      extractionMethod: extractionMethod || 'DIRECT_DOCUMENT_EXTRACTION',
      confidence,
      reviewStatus: ParameterReviewStatus.ACCEPTED_EVIDENCE_BACKED,
      evidenceSha256: evidence.sha256,
      updatedAt: timestamp,
    };

    const auditEvent = {
      eventId: `AUD-${Date.now().toString().slice(-6)}`,
      timestamp,
      actor,
      parameterId,
      parameterName,
      previousValue: 'None (Unpopulated)',
      newValue: `${extractedValue} ${unit || ''}`.trim(),
      evidenceSource: `${evidence.id} (${evidence.fileName})`,
      evidenceHash: evidence.sha256,
      reason: 'Extracted and validated from Accepted regulatory evidence artifact.',
    };

    return {
      updatedFacts: { ...existingFacts, [parameterId]: newFact },
      updatedConflicts: conflicts,
      updatedAuditLog: [auditEvent, ...auditLog],
      conflictCreated: false,
    };
  }

  // Case 2: Previous value exists and matches exactly -> Corroborate
  if (String(existingFact.value).trim() === String(extractedValue).trim()) {
    const auditEvent = {
      eventId: `AUD-${Date.now().toString().slice(-6)}`,
      timestamp,
      actor,
      parameterId,
      parameterName,
      previousValue: `${existingFact.value} ${existingFact.unit || ''}`.trim(),
      newValue: `${extractedValue} ${unit || ''}`.trim(),
      evidenceSource: `${evidence.id} (${evidence.fileName})`,
      evidenceHash: evidence.sha256,
      reason: 'Corroborating value verified from secondary accepted evidence.',
    };

    return {
      updatedFacts: existingFacts,
      updatedConflicts: conflicts,
      updatedAuditLog: [auditEvent, ...auditLog],
      conflictCreated: false,
    };
  }

  // Case 3: Conflicting value from different accepted evidence!
  // Mandatory Regulatory Rule: DO NOT automatically choose one!
  const conflictId = `CONF-${Date.now().toString().slice(-6)}`;
  const conflictObj = {
    conflictId,
    parameterId,
    parameterName,
    section,
    status: 'PENDING_RESOLUTION',
    candidateA: {
      value: existingFact.value,
      unit: existingFact.unit,
      sourceEvidenceId: existingFact.sourceEvidenceId,
      sourceFileName: existingFact.sourceFileName,
      sourceLocation: existingFact.sourceLocation,
      evidenceSha256: existingFact.evidenceSha256,
      extractionMethod: existingFact.extractionMethod,
      timestamp: existingFact.updatedAt,
    },
    candidateB: {
      value: extractedValue,
      unit: unit || existingFact.unit,
      sourceEvidenceId: evidence.id,
      sourceFileName: evidence.fileName,
      sourceLocation: location || 'Direct extraction',
      evidenceSha256: evidence.sha256,
      extractionMethod: extractionMethod || 'DIRECT_DOCUMENT_EXTRACTION',
      timestamp,
    },
    historicalCandidates: [
      {
        source: existingFact.sourceEvidenceId,
        fileName: existingFact.sourceFileName,
        value: existingFact.value,
        unit: existingFact.unit,
        sha256: existingFact.evidenceSha256,
      },
      {
        source: evidence.id,
        fileName: evidence.fileName,
        value: extractedValue,
        unit: unit || existingFact.unit,
        sha256: evidence.sha256,
      },
    ],
  };

  const conflictingFact = {
    ...existingFact,
    reviewStatus: ParameterReviewStatus.CONFLICTING,
    conflictId,
  };

  const auditEvent = {
    eventId: `AUD-${Date.now().toString().slice(-6)}`,
    timestamp,
    actor,
    parameterId,
    parameterName,
    previousValue: `${existingFact.value} ${existingFact.unit || ''}`.trim(),
    newValue: `CONFLICT DETECTED: [${existingFact.value}] vs [${extractedValue}]`,
    evidenceSource: `${existingFact.sourceEvidenceId} vs ${evidence.id}`,
    evidenceHash: `${existingFact.evidenceSha256?.substring(0, 8)}... / ${evidence.sha256?.substring(0, 8)}...`,
    reason: 'Discrepancy detected between two accepted evidence artifacts. Escalated for mandatory human engineering resolution.',
  };

  return {
    updatedFacts: { ...existingFacts, [parameterId]: conflictingFact },
    updatedConflicts: [conflictObj, ...conflicts],
    updatedAuditLog: [auditEvent, ...auditLog],
    conflictCreated: true,
    conflictId,
  };
}

/**
 * Resolve an existing parameter conflict via affirmative engineering decision.
 */
export function resolveParameterConflict({
  facts,
  conflicts,
  auditLog,
  conflictId,
  resolvedValue,
  selectedCandidateKey, // 'candidateA' | 'candidateB' | 'custom'
  rationale,
  actor = 'Designated Regulatory Engineer',
}) {
  const conflict = conflicts.find((c) => c.conflictId === conflictId);
  if (!conflict) throw new Error(`Conflict ${conflictId} not found.`);
  if (!rationale || !rationale.trim()) {
    throw new Error('Mandatory resolution rationale required for regulatory compliance.');
  }

  const timestamp = formatTimestamp();
  const fact = facts[conflict.parameterId];

  const sourceEvidenceId =
    selectedCandidateKey === 'candidateA'
      ? conflict.candidateA.sourceEvidenceId
      : selectedCandidateKey === 'candidateB'
      ? conflict.candidateB.sourceEvidenceId
      : `${conflict.candidateA.sourceEvidenceId} & ${conflict.candidateB.sourceEvidenceId}`;

  const sourceFileName =
    selectedCandidateKey === 'candidateA'
      ? conflict.candidateA.sourceFileName
      : selectedCandidateKey === 'candidateB'
      ? conflict.candidateB.sourceFileName
      : 'Engineering Reconciliation';

  const sourceLocation =
    selectedCandidateKey === 'candidateA'
      ? conflict.candidateA.sourceLocation
      : selectedCandidateKey === 'candidateB'
      ? conflict.candidateB.sourceLocation
      : 'Manual Reconciliation';

  const evidenceSha256 =
    selectedCandidateKey === 'candidateA'
      ? conflict.candidateA.evidenceSha256
      : selectedCandidateKey === 'candidateB'
      ? conflict.candidateB.evidenceSha256
      : `${conflict.candidateA.evidenceSha256}; ${conflict.candidateB.evidenceSha256}`;

  const resolvedFact = {
    ...fact,
    value: resolvedValue,
    sourceEvidenceId,
    sourceFileName,
    sourceLocation,
    evidenceSha256,
    reviewStatus: ParameterReviewStatus.ENGINEER_RESOLVED,
    conflictId: null,
    resolutionRationale: rationale,
    updatedAt: timestamp,
  };

  const updatedConflicts = conflicts.map((c) =>
    c.conflictId === conflictId
      ? {
          ...c,
          status: 'RESOLVED',
          resolvedValue,
          resolvedBy: actor,
          resolutionRationale: rationale,
          resolvedTimestamp: timestamp,
        }
      : c
  );

  const auditEvent = {
    eventId: `AUD-${Date.now().toString().slice(-6)}`,
    timestamp,
    actor,
    parameterId: conflict.parameterId,
    parameterName: conflict.parameterName,
    previousValue: `Conflict: [${conflict.candidateA.value}] vs [${conflict.candidateB.value}]`,
    newValue: `${resolvedValue} ${fact.unit || ''}`.trim(),
    evidenceSource: `${sourceEvidenceId} (${sourceFileName})`,
    evidenceHash: evidenceSha256,
    reason: `Conflict resolved by engineer: ${rationale}`,
  };

  return {
    updatedFacts: { ...facts, [conflict.parameterId]: resolvedFact },
    updatedConflicts,
    updatedAuditLog: [auditEvent, ...auditLog],
  };
}
