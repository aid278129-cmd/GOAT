import React from 'react';

/**
 * ContextualAssessmentCard
 * 
 * Rendered when a product compliance / standards inquiry is detected.
 * Prompts: "Let's assess your product."
 * Provides a clean launchpad directly into the 7-stage contextual compliance compiler.
 */
export function ContextualAssessmentCard({
  productName = 'ThermoSteel Vacuum Flask (1000ml)',
  standardNumber = 'IS 17526:2021',
  standardTitle = 'Vacuum Insulated Stainless Steel Domestic Containers',
  qcoStatus = 'Mandatory Gazette Quality Control Order',
  onStartAssessment,
  onCustomSpecIntake,
  onInspectStandard,
}) {
  return (
    <div className="mt-3.5 bg-gradient-to-br from-blue-50/80 via-white to-slate-50 border border-blue-200/90 rounded-xl p-4 sm:p-5 shadow-xs transition-all">
      {/* Header chip & status */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-800 bg-blue-100/80 px-2 py-0.5 rounded-md border border-blue-200">
            Contextual Product Assessment
          </span>
        </div>
        <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
          <span className="material-symbols-outlined text-[13px]">gavel</span>
          <span>{qcoStatus}</span>
        </span>
      </div>

      {/* Product & Standard details */}
      <div className="space-y-2 mb-4">
        <div>
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Target Product
          </div>
          <div className="text-sm sm:text-base font-bold text-slate-900">
            {productName}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              {standardNumber}
            </span>
            <span className="text-[11px] text-slate-500 font-medium">
              Statutory Gazette Scope
            </span>
          </div>
          <p className="text-xs text-slate-700 mt-1.5 leading-relaxed">
            {standardTitle}
          </p>
          <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
            <span>&bull; Double-wall hermetic vacuum</span>
            <span>&bull; Austenitic SS 304 food-contact</span>
            <span>&bull; Scheme I (ISI Mark)</span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 pt-1">
        <button
          type="button"
          onClick={() => onStartAssessment && onStartAssessment('golden')}
          className="flex-1 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs hover:shadow transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span>Open Product Assessment Workspace</span>
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </button>

        <button
          type="button"
          onClick={() => onStartAssessment && onStartAssessment('input')}
          className="py-2.5 px-3.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium border border-slate-200 transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-2xs"
          title="Input custom specifications for this assessment"
        >
          <span className="material-symbols-outlined text-[16px] text-slate-500">edit_note</span>
          <span>Custom Spec</span>
        </button>
      </div>

      <div className="text-[10px] text-slate-400 mt-2.5 text-center sm:text-left">
        Deterministic compiler evaluates Product DNA &rarr; Applicability &rarr; Requirements &rarr; Evidence &rarr; Gaps &rarr; Actions &rarr; Passport. Zero LLM compliance authority.
      </div>
    </div>
  );
}
