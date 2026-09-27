import React from 'react';

const STATUS_CONFIGS = {
  // Compliance statuses
  SATISFIED: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.2)]',
    dot: 'bg-emerald-400',
    label: 'SATISFIED',
  },
  POTENTIALLY_SATISFIED: {
    bg: 'bg-teal-950/60 text-teal-300 border-teal-500/40',
    dot: 'bg-teal-400',
    label: 'POTENTIALLY SATISFIED',
  },
  MISSING_EVIDENCE: {
    bg: 'bg-amber-950/60 text-amber-300 border-amber-500/40',
    dot: 'bg-amber-400 animate-pulse',
    label: 'MISSING EVIDENCE',
  },
  MORE_INFORMATION_REQUIRED: {
    bg: 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40',
    dot: 'bg-cyan-400',
    label: 'CLARIFICATION NEEDED',
  },
  POTENTIAL_GAP: {
    bg: 'bg-rose-950/60 text-rose-300 border-rose-500/40',
    dot: 'bg-rose-400',
    label: 'POTENTIAL GAP',
  },
  NOT_APPLICABLE: {
    bg: 'bg-slate-900 text-slate-400 border-slate-700',
    dot: 'bg-slate-500',
    label: 'NOT APPLICABLE',
  },
  CONFLICTING_EVIDENCE: {
    bg: 'bg-purple-950/60 text-purple-300 border-purple-500/40',
    dot: 'bg-purple-400',
    label: 'CONFLICTING EVIDENCE',
  },
  REQUIRES_EXPERT_REVIEW: {
    bg: 'bg-orange-950/60 text-orange-300 border-orange-500/40',
    dot: 'bg-orange-400',
    label: 'EXPERT REVIEW',
  },
  EXPERT_REVIEW_REQUIRED: {
    bg: 'bg-orange-950/60 text-orange-300 border-orange-500/40',
    dot: 'bg-orange-400',
    label: 'EXPERT REVIEW REQUIRED',
  },
  CONFLICTING_RULES: {
    bg: 'bg-rose-950/60 text-rose-300 border-rose-500/40',
    dot: 'bg-rose-400',
    label: 'CONFLICTING RULES',
  },
  COVERAGE_GAP: {
    bg: 'bg-purple-950/60 text-purple-300 border-purple-500/40',
    dot: 'bg-purple-400',
    label: 'COVERAGE GAP',
  },
  // Layer 5 Canonical Applicability statuses
  APPLICABLE: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.2)]',
    dot: 'bg-emerald-400',
    label: 'APPLICABLE',
  },
  POTENTIALLY_APPLICABLE: {
    bg: 'bg-sky-950/60 text-sky-300 border-sky-500/40',
    dot: 'bg-sky-400',
    label: 'POTENTIALLY APPLICABLE',
  },
  LIKELY_APPLICABLE: {
    bg: 'bg-indigo-950/60 text-indigo-300 border-indigo-500/40',
    dot: 'bg-indigo-400',
    label: 'LIKELY APPLICABLE',
  },
  POSSIBLY_APPLICABLE: {
    bg: 'bg-sky-950/60 text-sky-300 border-sky-500/40',
    dot: 'bg-sky-400',
    label: 'POSSIBLY APPLICABLE',
  },
  // Scope states
  IN_SCOPE: {
    bg: 'bg-teal-950/60 text-teal-300 border-teal-500/40',
    dot: 'bg-teal-400',
    label: 'IN SCOPE',
  },
  OUT_OF_SCOPE: {
    bg: 'bg-slate-900 text-slate-400 border-slate-700',
    dot: 'bg-slate-500',
    label: 'OUT OF SCOPE',
  },
  SCOPE_UNCERTAIN: {
    bg: 'bg-amber-950/60 text-amber-300 border-amber-500/40',
    dot: 'bg-amber-400',
    label: 'SCOPE UNCERTAIN',
  },
  // QCO Mandate states
  MANDATORY_QCO: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40 font-bold shadow-[0_0_8px_rgba(16,185,129,0.2)]',
    dot: 'bg-emerald-400',
    label: 'MANDATORY QCO',
  },
  VOLUNTARY: {
    bg: 'bg-slate-900 text-slate-300 border-slate-700',
    dot: 'bg-slate-500',
    label: 'VOLUNTARY STANDARD',
  },
  // Evidence statuses
  ACCEPTED: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40',
    dot: 'bg-emerald-400',
    label: 'ACCEPTED',
  },
  PENDING: {
    bg: 'bg-amber-950/60 text-amber-300 border-amber-500/40',
    dot: 'bg-amber-400',
    label: 'PENDING',
  },
  REJECTED: {
    bg: 'bg-rose-950/60 text-rose-300 border-rose-500/40',
    dot: 'bg-rose-400',
    label: 'REJECTED',
  },
  SUPERSEDED: {
    bg: 'bg-slate-900 text-slate-400 border-slate-700',
    dot: 'bg-slate-500',
    label: 'SUPERSEDED',
  },
  // Verification states
  SELF_DECLARED: {
    bg: 'bg-slate-900 text-slate-300 border-slate-700',
    dot: 'bg-slate-500',
    label: 'SELF DECLARED',
  },
  LAB_VERIFIED: {
    bg: 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40',
    dot: 'bg-cyan-400',
    label: 'LAB VERIFIED',
  },
  AUDITOR_APPROVED: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40',
    dot: 'bg-emerald-400',
    label: 'AUDITOR APPROVED',
  },
  // CAD / Spatial verification states
  BOUNDS_VERIFIED: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40',
    dot: 'bg-emerald-400',
    label: 'BOUNDS VERIFIED',
  },
  GEOMETRY_CONFIRMED: {
    bg: 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40',
    dot: 'bg-cyan-400',
    label: 'GEOMETRY CONFIRMED',
  },
  DIMENSION_MISMATCH: {
    bg: 'bg-rose-950/60 text-rose-300 border-rose-500/40',
    dot: 'bg-rose-400',
    label: 'DIMENSION MISMATCH',
  },
  // Job statuses
  IN_PROGRESS: {
    bg: 'bg-sky-950/60 text-sky-300 border-sky-500/40',
    dot: 'bg-sky-400 animate-pulse',
    label: 'IN PROGRESS',
  },
  COMPLETED: {
    bg: 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40',
    dot: 'bg-emerald-400',
    label: 'COMPLETED',
  },
  UNDER_REVIEW: {
    bg: 'bg-amber-950/60 text-amber-300 border-amber-500/40',
    dot: 'bg-amber-400',
    label: 'UNDER REVIEW',
  },
  DISPATCHED: {
    bg: 'bg-purple-950/60 text-purple-300 border-purple-500/40',
    dot: 'bg-purple-400',
    label: 'LAB DISPATCHED',
  },
};

export function StatusBadge({
  status,
  label: customLabel,
  size = 'md',
  showDot = true,
  className = '',
}) {
  const normKey = (status || '').toUpperCase().replace(/[\s-]/g, '_');
  const cfg = STATUS_CONFIGS[normKey] || {
    bg: 'bg-slate-900 text-slate-300 border-slate-700',
    dot: 'bg-slate-400',
    label: status ? status.replace(/_/g, ' ') : 'UNKNOWN',
  };

  const displayText = customLabel || cfg.label;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1',
    md: 'text-[11px] px-2.5 py-0.5 gap-1.5',
    lg: 'text-xs px-3 py-1 gap-2 font-bold',
  }[size] || 'text-[11px] px-2.5 py-0.5 gap-1.5';

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold rounded-full border ${cfg.bg} ${sizeClasses} ${className} shrink-0`}
    >
      {showDot && (
        <span
          className={`rounded-full shrink-0 ${cfg.dot} ${
            size === 'sm' ? 'w-1.5 h-1.5' : size === 'lg' ? 'w-2 h-2' : 'w-1.5 h-1.5'
          }`}
          aria-hidden="true"
        />
      )}
      <span className="truncate leading-none">{displayText}</span>
    </span>
  );
}

export default StatusBadge;
