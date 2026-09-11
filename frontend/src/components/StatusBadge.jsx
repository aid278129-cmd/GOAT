import React from 'react';

const STATUS_CONFIGS = {
  // Compliance statuses
  SATISFIED: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    label: 'SATISFIED',
  },
  POTENTIALLY_SATISFIED: {
    bg: 'bg-teal-50 text-teal-700 border-teal-200',
    dot: 'bg-teal-500',
    label: 'POTENTIALLY SATISFIED',
  },
  MISSING_EVIDENCE: {
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    label: 'MISSING EVIDENCE',
  },
  MORE_INFORMATION_REQUIRED: {
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    label: 'CLARIFICATION NEEDED',
  },
  POTENTIAL_GAP: {
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    label: 'POTENTIAL GAP',
  },
  NOT_APPLICABLE: {
    bg: 'bg-slate-100 text-slate-600 border-slate-200',
    dot: 'bg-slate-400',
    label: 'NOT APPLICABLE',
  },
  CONFLICTING_EVIDENCE: {
    bg: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    label: 'CONFLICTING EVIDENCE',
  },
  REQUIRES_EXPERT_REVIEW: {
    bg: 'bg-orange-50 text-orange-700 border-orange-200',
    dot: 'bg-orange-500',
    label: 'EXPERT REVIEW',
  },
  EXPERT_REVIEW_REQUIRED: {
    bg: 'bg-orange-50 text-orange-700 border-orange-200',
    dot: 'bg-orange-500',
    label: 'EXPERT REVIEW REQUIRED',
  },
  CONFLICTING_RULES: {
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    label: 'CONFLICTING RULES',
  },
  COVERAGE_GAP: {
    bg: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    label: 'COVERAGE GAP',
  },
  // Layer 5 Canonical Applicability statuses
  APPLICABLE: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    label: 'APPLICABLE',
  },
  POTENTIALLY_APPLICABLE: {
    bg: 'bg-sky-50 text-sky-700 border-sky-200',
    dot: 'bg-sky-500',
    label: 'POTENTIALLY APPLICABLE',
  },
  LIKELY_APPLICABLE: {
    bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    dot: 'bg-indigo-500',
    label: 'LIKELY APPLICABLE',
  },
  POSSIBLY_APPLICABLE: {
    bg: 'bg-sky-50 text-sky-700 border-sky-200',
    dot: 'bg-sky-500',
    label: 'POSSIBLY APPLICABLE',
  },
  // Scope states
  IN_SCOPE: {
    bg: 'bg-teal-50 text-teal-700 border-teal-200',
    dot: 'bg-teal-500',
    label: 'IN SCOPE',
  },
  OUT_OF_SCOPE: {
    bg: 'bg-slate-100 text-slate-600 border-slate-200',
    dot: 'bg-slate-400',
    label: 'OUT OF SCOPE',
  },
  SCOPE_UNCERTAIN: {
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    label: 'SCOPE UNCERTAIN',
  },
  // QCO Mandate states
  MANDATORY_QCO: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold',
    dot: 'bg-emerald-500',
    label: 'MANDATORY QCO',
  },
  VERIFIED_MANDATORY_QCO: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold',
    dot: 'bg-emerald-500',
    label: 'VERIFIED MANDATORY QCO',
  },
  VOLUNTARY: {
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    label: 'VOLUNTARY STANDARD',
  },
  NOT_GOVERNED_BY_QCO: {
    bg: 'bg-slate-100 text-slate-600 border-slate-200',
    dot: 'bg-slate-400',
    label: 'NOT GOVERNED BY QCO',
  },
  COVERAGE_NOT_ESTABLISHED: {
    bg: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    label: 'COVERAGE NOT ESTABLISHED',
  },
  // Layer 6 Retrieval Confidence Badges
  STRONG_MATCH: {
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold',
    dot: 'bg-emerald-500',
    label: 'STRONG MATCH',
  },
  UNCERTAIN_MATCH: {
    bg: 'bg-amber-50 text-amber-700 border-amber-200 font-medium',
    dot: 'bg-amber-500',
    label: 'UNCERTAIN MATCH',
  },
  NO_RELIABLE_MATCH: {
    bg: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    label: 'NO RELIABLE MATCH',
  },
  INSUFFICIENT_VERIFIED_EVIDENCE: {
    bg: 'bg-slate-100 text-slate-700 border-slate-300',
    dot: 'bg-slate-400',
    label: 'INSUFFICIENT VERIFIED EVIDENCE',
  },
  CLAUSE_TEXT_UNAVAILABLE: {
    bg: 'bg-amber-50 text-amber-700 border-amber-300 font-semibold',
    dot: 'bg-amber-500',
    label: 'CLAUSE TEXT UNAVAILABLE',
  },
  NOT_IN_KNOWLEDGE_BASE: {
    bg: 'bg-rose-50 text-rose-700 border-rose-300 font-semibold',
    dot: 'bg-rose-500',
    label: 'NOT IN KNOWLEDGE BASE',
  },
  // General
  READY: {
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    label: 'FOUNDATION READY',
  },
  PLANNED_FOR_M1: {
    bg: 'bg-slate-100 text-slate-600 border-slate-200',
    dot: 'bg-slate-400',
    label: 'PLANNED FOR M1',
  },
};

export function StatusBadge({ status, customLabel }) {
  const config = STATUS_CONFIGS[status] || {
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    label: status || 'UNKNOWN',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config.bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`}></span>
      {customLabel || config.label}
    </span>
  );
}
