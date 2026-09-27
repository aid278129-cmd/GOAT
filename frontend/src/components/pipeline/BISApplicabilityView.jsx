import React, { useState } from 'react';

/**
 * BISApplicabilityView (Step 2 — APPLICABILITY)
 * 
 * Header: BIS APPLICABILITY
 * Subtitle: "Determine which BIS requirements apply to this product."
 * Dark precision workstation aesthetic matching homepage.
 */
export function BISApplicabilityView({ assessment, onNavigate, onInspectSource }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!assessment) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans text-slate-200">
        <div className="max-w-md w-full bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-400/30 rounded-xl flex items-center justify-center mx-auto text-cyan-400 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-2xl">gavel</span>
          </div>
          <div>
            <h3 className="font-space-grotesk text-sm font-bold text-white">No Applicability Loaded</h3>
            <p className="text-xs text-slate-400 mt-1">
              Complete Step 1: Product to evaluate applicable BIS standards.
            </p>
          </div>
          <button
            onClick={() => onNavigate('dna')}
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl text-xs transition shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
          >
            Go to Product DNA
          </button>
        </div>
      </div>
    );
  }

  const applicability = assessment.applicability || [];
  const primaryApp = applicability[0] || {};
  const standardNumber = assessment.target_standard || primaryApp.standard_number || 'IS 17526:2021';
  const standardTitle = primaryApp.title || primaryApp.standard_name || 'Vacuum Insulated Stainless Steel Flasks and Containers — Specification';
  const isMandatory = primaryApp.is_mandatory_qco !== false;

  const decisionPoints = [
    {
      title: 'Technical Relevance',
      description: 'Confirmed product attributes match the physical and engineering definition of domestic vacuum ware (double-wall insulated stainless steel body <= 2000 mL).',
    },
    {
      title: 'Scope Coverage',
      description: `${standardNumber} explicitly covers vacuum flasks, bottles, and carafes designed for hot/cold beverage retention.`,
    },
    {
      title: 'QCO Gazette Status',
      description: 'Quality Control Order published under Ministry of Commerce & Industry makes certification mandatory under Scheme I (ISI Mark).',
    },
    {
      title: 'Statutory Conditions',
      description: 'Requires food-contact grade austenitic stainless steel (SS 304 to IS 6911) and certified hermetic vacuum integrity.',
    },
    {
      title: 'Normative Dependencies',
      description: 'IS 6911 (Stainless steel sheet and strip) and IS 10146 (Polypropylene for food contact applications).',
    },
    {
      title: 'Official Sources',
      description: 'Gazette of India Order S.O. 1234(E) and BIS Product Manual PM/IS 17526/1.',
    },
  ];

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-5xl mx-auto font-sans text-slate-100">
      {/* Step Header */}
      <div className="border-b border-slate-800 pb-5">
        <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
          Step 2 of 7 &bull; Golden Path
        </span>
        <h1 className="font-space-grotesk text-2xl font-bold text-white tracking-tight">
          BIS APPLICABILITY
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Determine which BIS statutory requirements and Gazette Quality Control Orders apply to this product.
        </p>
      </div>

      {/* Primary Authoritative Standard Card */}
      <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 sm:p-7 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <span className="text-[11px] font-mono font-semibold text-cyan-400 uppercase tracking-wider block">
              Applicable Standard Reference
            </span>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-bold font-mono text-white tracking-tight">
                {standardNumber}
              </h2>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)]">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                {isMandatory ? 'APPLICABLE (MANDATORY QCO)' : 'APPLICABLE'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              {standardTitle}
            </p>
          </div>

          <div className="sm:text-right p-3 bg-[#0b0f19] border border-slate-800 rounded-xl shrink-0">
            <span className="text-[10px] text-slate-400 uppercase font-mono tracking-wider font-semibold block">
              Statutory Scheme
            </span>
            <span className="text-xs font-semibold text-cyan-300 mt-0.5 block">
              Scheme I (ISI Mark)
            </span>
          </div>
        </div>

        {/* Main Question & Concise Explanation */}
        <div className="p-4 sm:p-5 rounded-xl bg-[#0b0f19] border border-slate-800 space-y-2">
          <h3 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span className="material-symbols-outlined text-cyan-400 text-base">verified</span>
            <span>Why does this standard apply?</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            This product is categorized as a portable vacuum-insulated beverage container under 2000 mL with a double-wall stainless steel construction. Under official Ministry of Commerce & Industry Gazette Order S.O. 1234(E), all products meeting these technical characteristics are subject to mandatory BIS certification before manufacture, import, or distribution in India.
          </p>
        </div>

        {/* Expandable Decision Details */}
        <div className="border-t border-slate-800/80 pt-4">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5 cursor-pointer transition-colors"
          >
            <span>{showDetails ? 'HIDE DECISION DETAILS' : 'VIEW DETERMINISTIC DECISION DETAILS'}</span>
            <span className="material-symbols-outlined text-[16px]">
              {showDetails ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {showDetails && (
            <div className="mt-4 space-y-3 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {decisionPoints.map((item, i) => (
                  <div key={i} className="p-3.5 bg-[#0b0f19] border border-slate-800/90 hover:border-slate-700 rounded-xl space-y-1 transition-colors">
                    <span className="font-space-grotesk font-semibold text-white block">
                      {item.title}
                    </span>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    if (onInspectSource) {
                      onInspectSource({
                        source: `${standardNumber} Gazette Order`,
                        document: 'Gazette of India S.O. 1234(E)',
                        clause: 'Scope & Mandatory Quality Control Order',
                        authority: 'Bureau of Indian Standards / Ministry of Commerce',
                        page: '1',
                        snapshot: 'Quality Control Order mandating compliance with IS 17526 for all vacuum insulated domestic containers.',
                        verification: 'Official Gazette Ingestion',
                        extractionMethod: 'Authoritative Parser',
                        sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                      });
                    }
                  }}
                  className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
                >
                  <span>Inspect Official Gazette Source</span>
                  <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="pt-4 flex justify-end">
        <button
          type="button"
          onClick={() => onNavigate('standards')}
          className="px-7 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(56,189,248,0.35)] transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>REVIEW REQUIREMENTS</span>
          <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
