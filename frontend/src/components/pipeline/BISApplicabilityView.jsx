import React from 'react';
import { StatusBadge } from '../StatusBadge';

export function BISApplicabilityView({ assessment, onNavigate }) {
  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">gavel</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Applicability Analysis</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              No product is currently selected. Select an assessment or enter product information in Step 1 to compute deterministic BIS applicability.
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

  const applicability = assessment.applicability || [];
  const primaryStandard = assessment.target_standard || (applicability[0]?.standard_number) || 'Pending Scoping';
  const clarifications = assessment.clarifications || [];

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 03 / 08 &bull; Layer 5 Applicability Engine
            </span>
            <span className="text-xs text-slate-500">Deterministic Regulatory Scoping &bull; 0% LLM Authority</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>BIS Standards Applicability & QCO Mandates</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Rule-based evaluation matching confirmed Product DNA against the Bureau of Indian Standards catalog and official Gazette QCOs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('clauses')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Inspect Clauses & Requirements</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Decision Order Pipeline Bar */}
      <div className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-600">
          <span className="font-bold text-slate-900">Deterministic Pipeline:</span>
          <span>Product DNA</span>
          <span className="text-slate-400">&rarr;</span>
          <span>Catalog Match</span>
          <span className="text-slate-400">&rarr;</span>
          <span>Scope Conditions</span>
          <span className="text-slate-400">&rarr;</span>
          <span>Gazette QCO Status</span>
          <span className="text-slate-400">&rarr;</span>
          <span className="font-bold text-emerald-700">Authoritative State</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Zero LLM Scoring</span>
        </div>
      </div>

      {/* Missing Discriminator Callout if applicable */}
      {clarifications.length > 0 && (
        <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-amber-900">
            <span className="material-symbols-outlined text-amber-700 text-base">info</span>
            <span>
              <strong>{clarifications.length} missing factor(s)</strong> detected. Standard scope is conditionally pending confirmation.
            </span>
          </div>
          <button
            onClick={() => onNavigate('dna')}
            className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white font-semibold shrink-0 cursor-pointer text-xs"
          >
            Resolve in Product DNA
          </button>
        </div>
      )}

      {/* Candidate Standards Matrix */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
            <span className="material-symbols-outlined text-slate-600 text-sm">assignment</span>
            <span>Evaluated Standard Candidates ({applicability.length})</span>
          </h2>
          <span className="text-[11px] font-mono text-slate-500">
            Primary Target: <strong className="text-slate-900">{primaryStandard}</strong>
          </span>
        </div>

        {applicability.length === 0 ? (
          <div className="p-6 rounded-lg bg-white border border-slate-200 text-xs text-center space-y-1">
            <p className="font-semibold text-slate-700">No applicable standards identified yet</p>
            <p className="text-slate-500">
              No gazetted BIS standards matched the provided product attributes. Update product specifications in Step 1 or Step 2.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {applicability.map((app, idx) => {
              const stdNum = app.standard_number || app.standard || 'IS Standard';
              const title = app.title || app.standard_name || 'Indian Standard Specification';
              const status = app.status || app.applicability_status || 'APPLICABLE';
              const scopeStatus = app.scope_status || 'IN_SCOPE';
              const qcoStatus = app.qco_status || (app.is_mandatory_qco ? 'MANDATORY_QCO' : 'VOLUNTARY');
              const edition = app.edition || app.version || 'Current Gazette Edition';
              const provenance = app.provenance || 'BIS Official Gazette Order';
              const reason = app.reason || app.applicability_reason || 'Product technical specification matches statutory standard scope.';

              return (
                <div
                  key={idx}
                  className="p-5 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-4 hover:border-slate-300 transition"
                >
                  {/* Top Card Row */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sm text-slate-900">{stdNum}</span>
                        <span className="text-[11px] font-mono text-slate-400">&bull;</span>
                        <span className="text-[11px] font-mono text-slate-600">{edition}</span>
                      </div>
                      <h3 className="text-xs font-semibold text-slate-700 mt-0.5">{title}</h3>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge status={status} />
                      {qcoStatus === 'MANDATORY_QCO' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200">
                          QCO MANDATORY
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Scoping Rationale */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Deterministic Scoping Rationale:</span>
                    <p className="text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-2.5 rounded border border-slate-100">
                      {reason}
                    </p>
                  </div>

                  {/* Metadata Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 text-[11px]">
                    <div className="p-2 rounded bg-slate-50 border border-slate-100 space-y-0.5">
                      <span className="text-[10px] uppercase text-slate-400 font-mono">Scope Status</span>
                      <div className="font-mono font-semibold text-slate-800">{scopeStatus}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 border border-slate-100 space-y-0.5">
                      <span className="text-[10px] uppercase text-slate-400 font-mono">Regulatory Order</span>
                      <div className="font-mono font-semibold text-slate-800">{qcoStatus}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 border border-slate-100 space-y-0.5">
                      <span className="text-[10px] uppercase text-slate-400 font-mono">Catalog Provenance</span>
                      <div className="font-mono font-semibold text-slate-800 truncate" title={provenance}>{provenance}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 border border-slate-100 space-y-0.5">
                      <span className="text-[10px] uppercase text-slate-400 font-mono">Standard Status</span>
                      <div className="font-mono font-semibold text-emerald-700">ACTIVE (GAZETTED)</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Regulatory Invariant Disclaimer */}
      <div className="p-3.5 rounded-lg bg-slate-100 border border-slate-200 text-[11px] text-slate-600 space-y-1">
        <div className="font-bold text-slate-800 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-xs text-slate-600">shield</span>
          <span>Layer 5 Legal Invariant: 0% LLM Compliance Authority</span>
        </div>
        <p className="leading-relaxed">
          Standard applicability is strictly computed by the deterministic Layer 5 rule engine against verified Bureau of Indian Standards gazette notifications and product taxonomies. User declarations and LLM reasoning do not possess regulatory authority.
        </p>
      </div>
    </div>
  );
}
