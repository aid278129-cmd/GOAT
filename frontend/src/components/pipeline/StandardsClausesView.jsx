import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function StandardsClausesView({ assessment, onNavigate }) {
  const [selectedClause, setSelectedClause] = useState(null);

  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">account_tree</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Standards Loaded</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Select an assessment or enter product information in Step 1 to inspect standard clauses and test parameters.
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

  const clauses = assessment.clauses || assessment.requirements || [];
  const primaryStandard = assessment.target_standard || (assessment.applicability?.[0]?.standard_number) || 'IS 17526:2021';

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 04 / 08 &bull; Standards & Clauses Decomposition
            </span>
            <span className="text-xs text-slate-500">Mandatory Test Parameters & Limits</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>{primaryStandard} &bull; Clause Breakdown</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Hierarchical breakdown of applicable clauses, requirements, test limits, and measurement units.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('evidence')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Proceed to Evidence Matrix</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Hierarchy Path Visual */}
      <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs flex flex-wrap items-center gap-2 text-xs font-mono">
        <span className="font-bold text-slate-900">Hierarchy:</span>
        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800">{primaryStandard}</span>
        <span className="text-slate-400">&rarr;</span>
        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800">Edition 2021 (Active)</span>
        <span className="text-slate-400">&rarr;</span>
        <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold">{clauses.length} Mandatory Clauses</span>
        <span className="text-slate-400">&rarr;</span>
        <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold">Test Parameters</span>
      </div>

      {/* Clauses Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-slate-600 text-sm">list_alt</span>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Mandatory Clauses & Specification Limits
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            {clauses.length} Clause Specifications Indexed
          </span>
        </div>

        {clauses.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 space-y-2">
            <p className="font-semibold text-slate-700">Clause-level source not currently verified.</p>
            <p className="text-slate-400 max-w-sm mx-auto">
              Full text acquisition for {primaryStandard} is in progress. Verified clauses will be displayed once gazette index verification completes.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-4">Clause #</th>
                  <th className="py-2.5 px-4">Requirement / Test Name</th>
                  <th className="py-2.5 px-4">Mandatory Limit & Parameters</th>
                  <th className="py-2.5 px-4">Test Unit</th>
                  <th className="py-2.5 px-4">Compliance Status</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {clauses.map((c, idx) => {
                  const clauseId = c.clause_id || c.clause || c.id || `Cl. ${idx + 1}`;
                  const title = c.title || c.requirement || c.name || 'Standard Requirement';
                  const limit = c.limit || c.specification_limit || c.expected_limit || c.description || 'Statutory Limit Defined';
                  const unit = c.unit || '—';
                  const status = c.status || (c.evaluation_status) || 'PENDING_EVIDENCE';

                  return (
                    <tr key={idx} className="hover:bg-slate-50 transition group">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900 group-hover:text-indigo-600 transition">
                        {clauseId}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">
                        {title}
                        {c.category && (
                          <span className="block text-[10px] font-mono font-normal text-slate-400">
                            {c.category}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700 max-w-xs truncate" title={limit}>
                        {limit}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500">
                        {unit}
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge status={status} />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedClause(c)}
                          className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-mono text-[11px] font-medium transition cursor-pointer"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected Clause Drawer / Modal */}
      {selectedClause && (
        <div className="p-4 rounded-lg bg-white border border-slate-300 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-slate-900">
                {selectedClause.clause_id || selectedClause.clause || 'Clause Details'}
              </span>
              <span className="text-xs text-slate-500">&bull; {selectedClause.title || selectedClause.requirement}</span>
            </div>
            <button
              onClick={() => setSelectedClause(null)}
              className="text-slate-400 hover:text-slate-700 text-xs font-mono cursor-pointer"
            >
              [Close]
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Requirement Specification:</span>
              <p className="text-slate-700 font-mono bg-slate-50 p-2.5 rounded border border-slate-200">
                {selectedClause.description || selectedClause.requirement || 'Standard specification requirement.'}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Test Limit & Protocol:</span>
              <p className="text-slate-700 font-mono bg-slate-50 p-2.5 rounded border border-slate-200">
                {selectedClause.limit || selectedClause.expected_limit || 'As per official BIS test methodology.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
