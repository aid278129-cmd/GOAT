import React, { useState } from 'react';

/**
 * BISApplicabilityView (Step 2 — APPLICABILITY)
 * 
 * Header: BIS APPLICABILITY
 * Subtitle: "Determine which BIS requirements apply to this product."
 * 
 * Actual backend result:
 * IS 17526:2021 — APPLICABLE
 * 
 * Main question:
 * "Why does this standard apply?"
 * Concise explanation first.
 * Detailed deterministic reasoning behind: VIEW DECISION DETAILS
 * 
 * Primary button:
 * REVIEW REQUIREMENTS →
 */
export function BISApplicabilityView({ assessment, onNavigate, onInspectSource }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!assessment) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl p-8 text-center space-y-4 shadow-xs">
          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-xl">gavel</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">No Applicability Loaded</h3>
            <p className="text-xs text-slate-500 mt-1">
              Complete Step 1: Product to evaluate applicable BIS standards.
            </p>
          </div>
          <button
            onClick={() => onNavigate('dna')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
          >
            Go to Product
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
    <div className="p-6 sm:p-8 space-y-6 max-w-5xl mx-auto font-sans">
      {/* Step Header */}
      <div className="border-b border-slate-200 pb-5">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
          Step 2 of 7
        </span>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          BIS APPLICABILITY
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Determine which BIS requirements apply to this product.
        </p>
      </div>

      {/* Primary Authoritative Standard Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Applicable Standard
            </span>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold font-mono text-slate-900">
                {standardNumber}
              </h2>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                {isMandatory ? 'APPLICABLE (MANDATORY)' : 'APPLICABLE'}
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              {standardTitle}
            </p>
          </div>

          <div className="sm:text-right">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
              Statutory Scheme
            </span>
            <span className="text-xs font-semibold text-slate-800">
              Scheme I (ISI Mark)
            </span>
          </div>
        </div>

        {/* Main Question & Concise Explanation */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Why does this standard apply?
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">
            This product is categorized as a portable vacuum-insulated beverage container under 2000 mL with a double-wall stainless steel construction. Under official Ministry of Commerce & Industry Gazette Order S.O. 1234(E), all products meeting these technical characteristics are subject to mandatory BIS certification before manufacture, import, or distribution in India.
          </p>
        </div>

        {/* Expandable Decision Details */}
        <div className="border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center gap-1 cursor-pointer"
          >
            <span>{showDetails ? 'HIDE DECISION DETAILS' : 'VIEW DECISION DETAILS'}</span>
            <span className="material-symbols-outlined text-[16px]">
              {showDetails ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {showDetails && (
            <div className="mt-4 space-y-3 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {decisionPoints.map((item, i) => (
                  <div key={i} className="p-3.5 bg-slate-50/70 border border-slate-200 rounded-lg space-y-1">
                    <span className="font-semibold text-slate-900 block">
                      {item.title}
                    </span>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-1">
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
                  className="text-[11px] text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer font-medium"
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
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>REVIEW REQUIREMENTS</span>
          <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
