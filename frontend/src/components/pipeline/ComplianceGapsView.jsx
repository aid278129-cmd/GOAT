import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function ComplianceGapsView({ assessment, onNavigate }) {
  const [filterState, setFilterState] = useState('ALL');

  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">troubleshoot</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Gaps Evaluated</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Select an assessment or enter product information in Step 1 to inspect deterministic compliance gaps.
            </p>
          </div>
          <button
            onClick={() => onNavigate('input')}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
          >
            Go to Product Input
          </button>
        </div>
      </div>
    );
  }

  const gaps = (assessment.gaps && assessment.gaps.length > 0)
    ? assessment.gaps
    : (assessment.compliance?.gap_register || assessment.compliance?.gaps || []);
  const primaryStandard = assessment.target_standard || (assessment.applicability?.[0]?.standard_number) || 'IS 17526:2021';

  // Counts
  const satisfiedCount = gaps.filter((g) => (g.status || g.result) === 'SATISFIED').length;
  const missingCount = gaps.filter((g) => (g.status || g.result) === 'MISSING' || (g.status || g.result) === 'MISSING_EVIDENCE').length;
  const partialCount = gaps.filter((g) => (g.status || g.result) === 'PARTIAL').length;
  const failedCount = gaps.filter((g) => (g.status || g.result) === 'FAILED').length;
  const expertCount = gaps.filter((g) => (g.status || g.result) === 'EXPERT_REVIEW_REQUIRED' || (g.status || g.result) === 'REQUIRES_EXPERT_REVIEW').length;

  const filteredGaps = filterState === 'ALL'
    ? gaps
    : gaps.filter((g) => {
        const s = g.status || g.result;
        if (filterState === 'SATISFIED') return s === 'SATISFIED';
        if (filterState === 'MISSING') return s === 'MISSING' || s === 'MISSING_EVIDENCE';
        if (filterState === 'ACTION_NEEDED') return s !== 'SATISFIED';
        return true;
      });

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 06 / 08 &bull; Layer 7 Deterministic Gap Engine
            </span>
            <span className="text-xs text-slate-500">Mathematical Compliance Gap Ledger</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Deterministic Compliance Gaps</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Evaluates requirement test limits directly against verified evidence. Focuses on: <em>What is missing and what should be done next?</em>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('actions')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Proceed to Lab & Remediation Actions</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Real Count Summary Cards (Zero fake percentages) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Total Clauses</span>
          <div className="text-2xl font-mono font-bold text-slate-900 mt-1">{gaps.length}</div>
          <span className="text-[10px] text-slate-500">Evaluated Under {primaryStandard}</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-emerald-600 font-bold">Satisfied</span>
          <div className="text-2xl font-mono font-bold text-emerald-700 mt-1">{satisfiedCount}</div>
          <span className="text-[10px] text-emerald-600">Verified by Test Evidence</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-amber-600 font-bold">Missing Evidence</span>
          <div className="text-2xl font-mono font-bold text-amber-700 mt-1">{missingCount}</div>
          <span className="text-[10px] text-amber-600">Pending Lab Test / Cert</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-rose-600 font-bold">Deficiencies</span>
          <div className="text-2xl font-mono font-bold text-rose-700 mt-1">{failedCount + partialCount}</div>
          <span className="text-[10px] text-rose-600">Non-Compliant Tolerances</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-purple-600 font-bold">Expert Review</span>
          <div className="text-2xl font-mono font-bold text-purple-700 mt-1">{expertCount}</div>
          <span className="text-[10px] text-purple-600">Engineering Ambiguity</span>
        </div>
      </div>

      {/* Safe Abstention Principle Callout */}
      <div className="p-3.5 rounded-lg bg-amber-50/70 border border-amber-200 text-xs text-amber-950 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div className="flex items-center gap-2 font-medium">
          <span className="material-symbols-outlined text-amber-700 text-base shrink-0">shield</span>
          <span>
            <strong>Safe Abstention Invariant:</strong> The compiler does not declare failure simply because proof is absent. It identifies the requirement, identifies the evidence needed, preserves the unresolved state, and generates the next engineering action.
          </span>
        </div>
        <span className="text-[10px] font-mono text-amber-800 bg-amber-100 px-2 py-0.5 rounded shrink-0 font-bold">
          Zero Fabricated Results
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 bg-slate-200/70 p-1 rounded text-xs font-mono">
          <button
            onClick={() => setFilterState('ALL')}
            className={`px-3 py-1 rounded transition cursor-pointer ${filterState === 'ALL' ? 'bg-white font-bold text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
          >
            All Clauses ({gaps.length})
          </button>
          <button
            onClick={() => setFilterState('ACTION_NEEDED')}
            className={`px-3 py-1 rounded transition cursor-pointer ${filterState === 'ACTION_NEEDED' ? 'bg-white font-bold text-amber-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
          >
            Action Needed ({missingCount + failedCount + partialCount + expertCount})
          </button>
          <button
            onClick={() => setFilterState('SATISFIED')}
            className={`px-3 py-1 rounded transition cursor-pointer ${filterState === 'SATISFIED' ? 'bg-white font-bold text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
          >
            Satisfied ({satisfiedCount})
          </button>
        </div>
      </div>

      {/* Gaps Table — Structured to Answer the 4 Cardinal Questions */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-4">1. Affected Requirement</th>
                <th className="py-2.5 px-4">2. Missing / Unverified Evidence</th>
                <th className="py-2.5 px-4">Deterministic State</th>
                <th className="py-2.5 px-4">3. Why Unresolved?</th>
                <th className="py-2.5 px-4 text-right">4. What Should Happen Next?</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredGaps.map((g, idx) => {
                const clauseId = g.clause_id || g.clause || `Cl. ${idx + 1}`;
                const title = g.requirement || g.title || 'Standard Test Limit';
                const evidence = g.evidence || g.evidence_snippet || g.attached_evidence || 'No evidence attached';
                let rawResult = g.status || g.result || 'MISSING_EVIDENCE';
                if (rawResult === 'MISSING') rawResult = 'MISSING_EVIDENCE';
                if (rawResult === 'VERIFIED') rawResult = 'SATISFIED';
                if (rawResult === 'FAILED') rawResult = 'NOT_SATISFIED';
                if (rawResult === 'REQUIRES_EXPERT_REVIEW') rawResult = 'EXPERT_REVIEW_REQUIRED';

                const reason = g.reason || g.evaluation_reason || 'Evidence missing or below statutory tolerance.';

                // Canonical Action Categories
                let action = g.required_action || g.suggested_action;
                if (!action || rawResult === 'SATISFIED') {
                  action = rawResult === 'SATISFIED' ? 'NO_ACTION_REQUIRED' : 'LAB_TEST_REQUIRED';
                }

                return (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    {/* 1. Affected Requirement */}
                    <td className="py-3 px-4 max-w-xs">
                      <span className="font-mono font-bold text-slate-900 block">{clauseId}</span>
                      <p className="font-semibold text-slate-800 text-[11px] mt-0.5">{title}</p>
                    </td>

                    {/* 2. Evidence Status */}
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-600 max-w-xs">
                      <span className="line-clamp-2" title={evidence}>
                        {evidence}
                      </span>
                    </td>

                    {/* Deterministic State */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {rawResult === 'SATISFIED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          SATISFIED
                        </span>
                      )}
                      {rawResult === 'MISSING_EVIDENCE' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-900 border border-amber-300" title="Missing evidence artifact — requires lab test report">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                          MISSING_EVIDENCE
                        </span>
                      )}
                      {rawResult === 'NOT_SATISFIED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                          NOT_SATISFIED
                        </span>
                      )}
                      {rawResult === 'EXPERT_REVIEW_REQUIRED' && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200">
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                          EXPERT_REVIEW_REQUIRED
                        </span>
                      )}
                      {rawResult !== 'SATISFIED' && rawResult !== 'MISSING_EVIDENCE' && rawResult !== 'NOT_SATISFIED' && rawResult !== 'EXPERT_REVIEW_REQUIRED' && (
                        <StatusBadge status={rawResult} />
                      )}
                    </td>

                    {/* 3. Why Unresolved? */}
                    <td className="py-3 px-4 text-slate-600 max-w-xs text-[11px]">
                      <p className="line-clamp-2 leading-relaxed" title={reason}>
                        {reason}
                      </p>
                    </td>

                    {/* 4. What Happens Next? */}
                    <td className="py-3 px-4 text-right whitespace-nowrap font-mono text-[10px]">
                      {action === 'NO_ACTION_REQUIRED' ? (
                        <span className="text-slate-400 font-normal">NO_ACTION_REQUIRED</span>
                      ) : (
                        <span className="px-2 py-1 rounded bg-slate-900 text-white font-bold tracking-tight">
                          {action}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
