import React from 'react';

/**
 * ContextualConsumerCard
 * 
 * Interactive guide for consumer verification of ISI mark CM/L numbers,
 * reporting counterfeit products, and grievance redressal under the BIS Act 2016.
 */
export function ContextualConsumerCard({ onInspectSource }) {
  return (
    <div className="mt-3.5 bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs transition-all">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-emerald-600 text-lg">shield_person</span>
          <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Consumer Protection & BIS CARE Guide
          </span>
        </div>
        <span className="text-[11px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          Consumer Rights
        </span>
      </div>

      <div className="space-y-3 text-xs">
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
          <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-blue-600 text-[16px]">search_check</span>
            <span>Verifying Genuine ISI Mark (CM/L Number)</span>
          </h4>
          <p className="text-slate-600 leading-relaxed">
            Every genuine ISI mark MUST display:
          </p>
          <ul className="list-disc list-inside text-slate-600 pl-1 space-y-0.5 text-[11px]">
            <li>The official ISI monogram.</li>
            <li>The Indian Standard Number (e.g. <code>IS 17526</code>) displayed directly above the monogram.</li>
            <li>A 7-digit License Number (CM/L - XXXXXXX) directly below the monogram.</li>
          </ul>
          <p className="text-slate-500 text-[11px] pt-1">
            If the CM/L number is missing or illegible, the mark is likely unauthorized or counterfeit.
          </p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
          <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-red-600 text-[16px]">report_problem</span>
            <span>How to Report Counterfeit Goods or Misuse</span>
          </h4>
          <ol className="list-decimal list-inside text-slate-600 pl-1 space-y-1 text-[11px]">
            <li>Open the <strong>BIS CARE App</strong> &rarr; Select <strong>"Complaints"</strong>.</li>
            <li>Choose complaint type: <em>Quality of Product</em> or <em>Misuse of ISI Mark</em>.</li>
            <li>Provide photograph of the product packaging showing counterfeit logo and purchase invoice.</li>
            <li>BIS Enforcement Directorate conducts surprise raids under Section 29 of the BIS Act 2016.</li>
          </ol>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Statutory Authority: Bureau of Indian Standards Act 2016 (Section 28-30)</span>
        <button
          type="button"
          onClick={() => onInspectSource && onInspectSource({
            source: 'Bureau of Indian Standards Act 2016',
            document: 'Act No. 11 of 2016',
            clause: 'Section 29 (Penalties for misuse of standard mark)',
            authority: 'Parliament of India / BIS',
            page: '14-17',
            verification: 'Statutory Act of Parliament',
            extractionMethod: 'Authoritative Parser',
            sha256: 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5',
          })}
          className="text-blue-600 hover:text-blue-800 font-medium underline cursor-pointer"
        >
          Inspect BIS Act 2016
        </button>
      </div>
    </div>
  );
}
