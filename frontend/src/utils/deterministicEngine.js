/**
 * GOAT Deterministic Standards & Clause Assessment Engine
 *
 * Traceability Path:
 * Standard -> Clause -> Requirement -> Product DNA Parameter -> Accepted Evidence -> Deterministic Rule -> Engineering Assessment
 *
 * REGULATORY MANDATE:
 * Operates ONLY on: Accepted Evidence -> Verified Product DNA -> Applicable Requirement.
 * Evaluator outputs are strictly classified under ENGINEERING ASSESSMENT and
 * NEVER presented as BIS Certification, BIS Approval, Laboratory Certification, or Statutory Attestation.
 */

import {
  ComparisonType,
  ProductDnaMatchState,
  EngineeringAssessmentState,
} from '../types/standardsTypes';

/**
 * Determine match status between a requirement and Product DNA repository
 */
export function getDnaMatchStatus(requirement, productDnaFacts = {}, conflictsList = []) {
  const paramKey = requirement.requiredParameterKey;

  if (!paramKey) {
    // If purely documentation or visual with no specific parameter key
    return ProductDnaMatchState.READY_FOR_ASSESSMENT;
  }

  // Check if parameter has an unresolved conflict
  const hasConflict = (conflictsList || []).some(
    (c) => c.parameterKey === paramKey && !c.resolved
  );
  if (hasConflict) {
    return ProductDnaMatchState.CONFLICTING_DNA;
  }

  const fact = productDnaFacts[paramKey];
  if (!fact) {
    return ProductDnaMatchState.NO_MATCHING_DNA;
  }

  // Check verification and evidence backing
  if (fact.reviewStatus === 'VERIFIED' && fact.evidenceId) {
    return ProductDnaMatchState.READY_FOR_ASSESSMENT;
  }

  return ProductDnaMatchState.DNA_AVAILABLE;
}

/**
 * Evaluate a single requirement deterministically
 */
export function evaluateRequirement({
  standard,
  requirement,
  productDnaFacts = {},
  conflictsList = [],
  evidenceList = [],
  ruleVersion = 'v1.0.0',
  kbVersion = 'KB-2026.1',
}) {
  const timestamp = new Date().toISOString();
  const assessmentId = `ASM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;

  // 1. Check if requirement is explicitly marked Not Applicable
  if (requirement.comparisonType === ComparisonType.NOT_APPLICABLE) {
    return createEvaluationResult({
      assessmentId,
      standard,
      requirement,
      engineeringResult: EngineeringAssessmentState.NOT_APPLICABLE,
      explanation: 'Statutory clause is outside the current product operational scope or rating envelope.',
      ruleVersion,
      kbVersion,
      timestamp,
    });
  }

  const paramKey = requirement.requiredParameterKey;

  // 2. Check for active unresolved conflict on the parameter
  const activeConflict = (conflictsList || []).find(
    (c) => c.parameterKey === paramKey && !c.resolved
  );
  if (activeConflict) {
    return createEvaluationResult({
      assessmentId,
      standard,
      requirement,
      engineeringResult: EngineeringAssessmentState.CONFLICT,
      explanation: `Parameter [${paramKey}] has an active unresolved conflict between evidence artifacts (${activeConflict.candidates?.map((c) => c.evidenceId).join(' vs ')}). Human resolution required before deterministic compilation.`,
      conflicts: [activeConflict],
      ruleVersion,
      kbVersion,
      timestamp,
    });
  }

  // 3. Retrieve Product DNA fact
  const fact = paramKey ? productDnaFacts[paramKey] : null;

  if (paramKey && !fact) {
    return createEvaluationResult({
      assessmentId,
      standard,
      requirement,
      engineeringResult: EngineeringAssessmentState.DATA_REQUIRED,
      explanation: `Statutory assessment blocked: Required parameter [${paramKey}] is not present in Product DNA facts repository.`,
      ruleVersion,
      kbVersion,
      timestamp,
    });
  }

  // 4. Verify that Product DNA fact is VERIFIED and backed by ACCEPTED evidence
  if (fact) {
    if (fact.reviewStatus !== 'VERIFIED') {
      return createEvaluationResult({
        assessmentId,
        standard,
        requirement,
        fact,
        engineeringResult: EngineeringAssessmentState.DATA_REQUIRED,
        explanation: `Statutory assessment blocked: Product DNA parameter [${paramKey}] has review status "${fact.reviewStatus}". Only VERIFIED parameters can be evaluated.`,
        ruleVersion,
        kbVersion,
        timestamp,
      });
    }

    const sourceEvidence = (evidenceList || []).find((e) => e.id === fact.evidenceId);
    if (!sourceEvidence || sourceEvidence.acceptanceStatus !== 'ACCEPTED') {
      return createEvaluationResult({
        assessmentId,
        standard,
        requirement,
        fact,
        sourceEvidence,
        engineeringResult: EngineeringAssessmentState.DATA_REQUIRED,
        explanation: `Evidence Gating Violation: Underlying source artifact [${fact.evidenceId}] is not ACCEPTED. Deterministic evaluation requires affirmative evidence acceptance.`,
        ruleVersion,
        kbVersion,
        timestamp,
      });
    }
  }

  // 5. If TEXT_REVIEW or subjective qualitative review, require human engineering sign-off
  if (requirement.comparisonType === ComparisonType.TEXT_REVIEW) {
    return createEvaluationResult({
      assessmentId,
      standard,
      requirement,
      fact,
      sourceEvidence: fact ? (evidenceList || []).find((e) => e.id === fact.evidenceId) : null,
      engineeringResult: EngineeringAssessmentState.HUMAN_REVIEW_REQUIRED,
      explanation: `Qualitative statutory clause requires certified engineering review: "${requirement.requirementText}". Observed fact: "${fact ? fact.value : 'N/A'}".`,
      ruleVersion,
      kbVersion,
      timestamp,
    });
  }

  // 6. Execute deterministic mathematical / logical rule
  const evaluation = runDeterministicRule(requirement, fact);

  return createEvaluationResult({
    assessmentId,
    standard,
    requirement,
    fact,
    sourceEvidence: fact ? (evidenceList || []).find((e) => e.id === fact.evidenceId) : null,
    engineeringResult: evaluation.resultState,
    explanation: evaluation.explanation,
    ruleCalculation: evaluation.details,
    ruleVersion,
    kbVersion,
    timestamp,
  });
}

/**
 * Execute the mathematical/logical comparison rule
 */
function runDeterministicRule(req, fact) {
  const comp = req.comparisonType;
  const rawVal = fact ? fact.value : null;

  if (rawVal === null || rawVal === undefined) {
    return {
      resultState: EngineeringAssessmentState.DATA_REQUIRED,
      explanation: 'No value available in Product DNA.',
      details: { comparison: comp, rawVal: null },
    };
  }

  // Numeric comparisons
  if (
    [
      ComparisonType.GREATER_THAN,
      ComparisonType.GREATER_THAN_OR_EQUAL,
      ComparisonType.LESS_THAN,
      ComparisonType.LESS_THAN_OR_EQUAL,
      ComparisonType.RANGE,
    ].includes(comp)
  ) {
    const numVal = parseFloat(String(rawVal).replace(/[^\d.-]/g, ''));
    if (isNaN(numVal)) {
      return {
        resultState: EngineeringAssessmentState.HUMAN_REVIEW_REQUIRED,
        explanation: `Value "${rawVal}" cannot be parsed as a deterministic number for rule ${comp}. Human inspection required.`,
        details: { rawVal, comp },
      };
    }

    if (comp === ComparisonType.GREATER_THAN) {
      const target = parseFloat(req.targetValue);
      const passed = numVal > target;
      return {
        resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
        explanation: `Condition [${numVal} > ${target} ${req.unit || ''}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
        details: { measured: numVal, operator: '>', target, passed },
      };
    }

    if (comp === ComparisonType.GREATER_THAN_OR_EQUAL) {
      const target = parseFloat(req.targetValue);
      const passed = numVal >= target;
      return {
        resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
        explanation: `Condition [${numVal} >= ${target} ${req.unit || ''}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
        details: { measured: numVal, operator: '>=', target, passed },
      };
    }

    if (comp === ComparisonType.LESS_THAN) {
      const target = parseFloat(req.targetValue);
      const passed = numVal < target;
      return {
        resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
        explanation: `Condition [${numVal} < ${target} ${req.unit || ''}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
        details: { measured: numVal, operator: '<', target, passed },
      };
    }

    if (comp === ComparisonType.LESS_THAN_OR_EQUAL) {
      const target = parseFloat(req.targetValue);
      const passed = numVal <= target;
      return {
        resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
        explanation: `Condition [${numVal} <= ${target} ${req.unit || ''}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
        details: { measured: numVal, operator: '<=', target, passed },
      };
    }

    if (comp === ComparisonType.RANGE) {
      const min = parseFloat(req.minValue);
      const max = parseFloat(req.maxValue);
      const passed = numVal >= min && numVal <= max;
      return {
        resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
        explanation: `Condition [${min} <= ${numVal} <= ${max} ${req.unit || ''}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
        details: { measured: numVal, min, max, passed },
      };
    }
  }

  // Exact Match
  if (comp === ComparisonType.EQUAL) {
    const s1 = String(rawVal).trim().toLowerCase();
    const s2 = String(req.targetValue).trim().toLowerCase();
    const passed = s1 === s2;
    return {
      resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
      explanation: `Exact match condition ["${rawVal}" == "${req.targetValue}"] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
      details: { measured: rawVal, target: req.targetValue, passed },
    };
  }

  // Enumeration
  if (comp === ComparisonType.ENUMERATION) {
    const allowed = Array.isArray(req.allowedValues)
      ? req.allowedValues.map((v) => String(v).trim().toLowerCase())
      : String(req.allowedValues || '')
          .split(',')
          .map((v) => v.trim().toLowerCase());
    const valLower = String(rawVal).trim().toLowerCase();
    const passed = allowed.includes(valLower);
    return {
      resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
      explanation: `Enumeration condition ["${rawVal}" in {${allowed.join(', ')}}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
      details: { measured: rawVal, allowed, passed },
    };
  }

  // Boolean
  if (comp === ComparisonType.BOOLEAN) {
    const str = String(rawVal).trim().toLowerCase();
    const boolVal = str === 'true' || str === 'yes' || str === 'pass' || str === '1';
    const targetBool = req.targetValue === true || String(req.targetValue).toLowerCase() === 'true';
    const passed = boolVal === targetBool;
    return {
      resultState: passed ? EngineeringAssessmentState.ENGINEERING_PASS : EngineeringAssessmentState.ENGINEERING_GAP,
      explanation: `Boolean statutory condition [measured: ${boolVal} == target: ${targetBool}] evaluated to ${passed ? 'SATISFIED' : 'NOT SATISFIED'}.`,
      details: { measured: boolVal, target: targetBool, passed },
    };
  }

  return {
    resultState: EngineeringAssessmentState.HUMAN_REVIEW_REQUIRED,
    explanation: `Unrecognized comparison type: ${comp}. Human engineering review required.`,
    details: { comp },
  };
}

/**
 * Format complete evaluation result with 7-stage Trace Chain and immutable Audit Record
 */
function createEvaluationResult({
  assessmentId,
  standard,
  requirement,
  fact = null,
  sourceEvidence = null,
  engineeringResult,
  explanation,
  ruleCalculation = null,
  conflicts = [],
  ruleVersion,
  kbVersion,
  timestamp,
}) {
  const traceChain = {
    standard: {
      id: standard?.id || 'UNASSIGNED',
      identifier: standard?.identifier || 'Statutory Standard',
      revisionYear: standard?.revisionYear || 'N/A',
      title: standard?.title || 'Statutory Specification',
    },
    clause: {
      clauseRef: requirement.clauseRef || 'Clause Reference Pending',
      part: requirement.part || 'General',
      section: requirement.section || 'General',
      subClause: requirement.subClause || '',
    },
    requirement: {
      reqId: requirement.reqId,
      text: requirement.requirementText,
      type: requirement.requirementType,
      parameterKey: requirement.requiredParameterKey,
      comparisonType: requirement.comparisonType,
      targetValue: requirement.targetValue,
      minValue: requirement.minValue,
      maxValue: requirement.maxValue,
      allowedValues: requirement.allowedValues,
      unit: requirement.unit,
      verificationMethod: requirement.verificationMethod,
      sourceReference: requirement.sourceReference,
    },
    productDna: fact
      ? {
          key: fact.parameterKey,
          label: fact.label,
          value: fact.value,
          unit: fact.unit,
          reviewStatus: fact.reviewStatus,
          confidence: fact.confidence,
          locationCitation: fact.locationCitation,
        }
      : null,
    evidence: sourceEvidence
      ? {
          id: sourceEvidence.id,
          fileName: sourceEvidence.fileName,
          fileType: sourceEvidence.fileType,
          acceptanceStatus: sourceEvidence.acceptanceStatus,
          sha256Hash: sourceEvidence.sha256Hash || fact?.evidenceHash || 'PENDING',
          locationCitation: fact?.locationCitation || 'Artifact Header',
        }
      : fact?.evidenceId
      ? {
          id: fact.evidenceId,
          fileName: fact.sourceFile || 'Evidence Artifact',
          acceptanceStatus: 'ACCEPTED',
          sha256Hash: fact.evidenceHash || 'UNKNOWN',
          locationCitation: fact.locationCitation,
        }
      : null,
    rule: {
      comparisonType: requirement.comparisonType,
      ruleCalculation,
    },
    engineeringResult,
  };

  const auditRecord = {
    assessmentId,
    requirementId: requirement.reqId,
    standardIdentifier: standard?.identifier || 'N/A',
    productDnaVersion: fact?.updatedAt || fact?.extractedAt || timestamp,
    evidenceIds: sourceEvidence ? [sourceEvidence.id] : fact?.evidenceId ? [fact.evidenceId] : [],
    evidenceHashes: [sourceEvidence?.sha256Hash || fact?.evidenceHash || 'NONE'],
    ruleVersion,
    knowledgeBaseVersion: kbVersion,
    timestamp,
    executionStatus: 'COMPLETED',
    engineeringResult,
    rationale: explanation,
  };

  return {
    assessmentId,
    requirementId: requirement.reqId,
    engineeringResult,
    explanation,
    traceChain,
    auditRecord,
    timestamp,
  };
}
