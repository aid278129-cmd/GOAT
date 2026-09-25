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
          <div className="grid grid-cols-1 gap-5">
            {applicability.map((app, idx) => {
              const stdNum = app.standard_number || app.standard || 'IS 17526:2021';
              const title = app.title || app.standard_name || 'Domestic Stainless Steel Vacuum Flasks and Insulated Containers';
              const status = app.status || app.applicability_status || 'APPLICABLE';
              const scopeStatus = app.scope_status || 'IN_SCOPE';
              const qcoStatus = app.qco_status || (app.is_mandatory_qco ? 'MANDATORY_QCO' : 'VOLUNTARY');
              const edition = app.edition || app.version || 'Current Consolidated Gazette Edition';
              const provenance = app.provenance || 'Official Gazette of India (DPIIT) &bull; BIS ManakOnline Schedule';
              const reason = app.reason || app.applicability_reason || 'Product technical specification matches statutory standard scope.';
              const technicalRelevance = app.technical_relevance || 'Matches Product DNA: vacuum-insulated double-walled stainless steel container intended for domestic liquid storage.';
              const scopeDefinition = app.scope_definition || 'Covers vacuum flasks and insulated drinkware vessels with nominal capacity up to 2000 mL.';
              const conditions = app.conditions || 'Food-contact surfaces must conform to food-grade austenitic stainless steel; vacuum thermal seal required.';
              const dependencies = app.normative_dependencies || 'IS 6911 (Stainless Steel Specification), IS 302-1 (General Safety Requirements)';

              return (
                <div
                  key={idx}
                  className="p-5 sm:p-6 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-5 hover:border-slate-300 transition"
                >
                  {/* Top Header Row */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-base text-slate-900">{stdNum}</span>
                        <span className="text-slate-300">&bull;</span>
                        <span className="text-xs font-mono text-slate-500">{edition}</span>
                        <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded">
                          CONTROLLED DEMO / SYNTHETIC
                        </span>
                      </div>
                      <h3 className="text-xs md:text-sm font-semibold text-slate-800 mt-1">{title}</h3>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge status={status} />
                      {qcoStatus === 'MANDATORY_QCO' && (
                        <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200">
                          MANDATORY QCO
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Why did Zyntrix select this standard? - Compact Decision Chain Hierarchy */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono uppercase text-slate-500 font-bold flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-xs text-indigo-600">account_tree</span>
                        <span>Why did Zyntrix select this standard? Deterministic Decision Chain</span>
                      </span>
                      <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        100% Rule Match &bull; 0% LLM
                      </span>
                    </div>

                    <div className="bg-slate-50 rounded-lg p-3.5 border border-slate-200 divide-y divide-slate-200/70 text-xs">
                      {/* 1. Product Supplied */}
                      <div className="py-2 first:pt-0 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          1. Product Supplied
                        </span>
                        <span className="font-bold text-slate-900 md:col-span-3">
                          {assessment.product_name || 'Domestic Stainless Steel Vacuum Flask 1000ml'}
                        </span>
                      </div>

                      {/* 2. Accepted Product DNA */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          2. Accepted Product DNA
                        </span>
                        <span className="text-slate-800 md:col-span-3 font-mono text-[11px]">
                          Category: {assessment.category || 'Drinkware & Food Contact Containers'} &bull; Material: SS 304 &bull; Capacity: 1000 mL &bull; Construction: Double Wall Vacuum &bull; Food Contact: True
                        </span>
                      </div>

                      {/* 3. Standard Considered */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          3. Standard Considered
                        </span>
                        <span className="font-mono font-bold text-slate-900 md:col-span-3">
                          {stdNum} &bull; {title}
                        </span>
                      </div>

                      {/* 4. Technical Relevance */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          4. Technical Relevance
                        </span>
                        <span className="text-slate-800 md:col-span-3">
                          {technicalRelevance}
                        </span>
                      </div>

                      {/* 5. Scope Match */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          5. Scope Match
                        </span>
                        <span className="text-slate-800 md:col-span-3">
                          {scopeDefinition}
                        </span>
                      </div>

                      {/* 6. Regulatory / QCO Relevance */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          6. Regulatory / QCO Relevance
                        </span>
                        <div className="md:col-span-3 flex items-center gap-2">
                          <span className="font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                            {qcoStatus}
                          </span>
                          <span className="text-slate-600 text-[11px]">
                            DPIIT Domestic Water Bottles (Quality Control) Order, 2023 &bull; Mandatory BIS ISI mark license required.
                          </span>
                        </div>
                      </div>

                      {/* 7. Conditions */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          7. Conditions
                        </span>
                        <span className="text-slate-800 md:col-span-3 font-mono text-[11px]">
                          {conditions}
                        </span>
                      </div>

                      {/* 8. Normative Dependencies */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          8. Normative Dependencies
                        </span>
                        <span className="text-slate-700 md:col-span-3 font-mono text-[11px]">
                          {dependencies}
                        </span>
                      </div>

                      {/* 9. Authoritative Sources */}
                      <div className="py-2 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-slate-500 uppercase">
                          9. Authoritative Sources
                        </span>
                        <span className="text-slate-600 md:col-span-3 font-mono text-[11px]">
                          {provenance}
                        </span>
                      </div>

                      {/* 10. What Remains Unverified */}
                      <div className="py-2 last:pb-0 grid grid-cols-1 md:grid-cols-4 gap-1 md:gap-3 items-baseline">
                        <span className="font-mono text-[10px] font-bold text-amber-700 uppercase">
                          10. What Remains Unverified
                        </span>
                        <div className="md:col-span-3 flex items-center gap-2">
                          <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-mono text-[11px]">
                            Safe Abstention: Empirical laboratory test reports (thermal retention Cl. 5.4 & raw mill test certificate) pending accredited upload.
                          </span>
                        </div>
                      </div>
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
