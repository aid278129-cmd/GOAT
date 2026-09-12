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

  const gaps = assessment.gaps || [];
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
          <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Total Requirements</span>
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
          <span className="text-[10px] text-amber-600">Requires Lab Test / Cert</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-rose-600 font-bold">Failed / Gaps</span>
          <div className="text-2xl font-mono font-bold text-rose-700 mt-1">{failedCount + partialCount}</div>
          <span className="text-[10px] text-rose-600">Specification Deficiencies</span>
        </div>

        <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs">
          <span className="text-[10px] font-mono uppercase text-purple-600 font-bold">Expert Review</span>
          <div className="text-2xl font-mono font-bold text-purple-700 mt-1">{expertCount}</div>
          <span className="text-[10px] text-purple-600">Regulatory Ambiguity</span>
        </div>
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

      {/* Gaps Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-4">Clause #</th>
                <th className="py-2.5 px-4">Requirement</th>
                <th className="py-2.5 px-4">Attached Evidence</th>
                <th className="py-2.5 px-4">Deterministic Result</th>
                <th className="py-2.5 px-4">Evaluation Rationale</th>
                <th className="py-2.5 px-4 text-right">Required Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredGaps.map((g, idx) => {
                const clauseId = g.clause_id || g.clause || `Cl. ${idx + 1}`;
                const title = g.requirement || g.title || 'Standard Test Limit';
                const evidence = g.evidence || g.evidence_snippet || g.attached_evidence || 'No evidence attached';
                const result = g.status || g.result || 'MISSING';
                const reason = g.reason || g.evaluation_reason || 'Evidence missing or below statutory tolerance.';
                const action = g.required_action || g.suggested_action || (result === 'SATISFIED' ? 'None (Conformity Documented)' : 'LAB_TEST_REQUIRED');

                return (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900 whitespace-nowrap">
                      {clauseId}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800 max-w-xs">
                      {title}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-600 max-w-xs">
                      <span className="line-clamp-2" title={evidence}>
                        {evidence}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <StatusBadge status={result} />
                    </td>
                    <td className="py-3 px-4 text-slate-600 max-w-xs">
                      <p className="line-clamp-2 leading-relaxed" title={reason}>
                        {reason}
                      </p>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap font-mono text-[11px]">
                      {result === 'SATISFIED' ? (
                        <span className="text-slate-400 font-normal">—</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
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
