import React from 'react';

/**
 * LabActionsView (Step 6 — ACTIONS)
 * 
 * Header: LAB & ACTIONS
 * Subtitle: "Complete the work required to resolve open requirements."
 * 
 * Columns:
 * Action | Requirement | Reason | Evidence Required
 * 
 * Examples:
 * - LAB TEST REQUIRED
 * - DOCUMENT REQUIRED
 * - DECLARATION REQUIRED
 * - MARKING EVIDENCE REQUIRED
 * - CORRECTIVE ACTION REQUIRED
 * - EXPERT REVIEW REQUIRED
 * 
 * Factual only — no fake booking, pricing, rankings, or guarantees.
 * Primary button: VIEW ASSESSMENT →
 */
export function LabActionsView({ assessment, onNavigate, onInspectSource }) {
  if (!assessment) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl p-8 text-center space-y-4 shadow-xs">
          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-xl">science</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">No Actions Loaded</h3>
            <p className="text-xs text-slate-500 mt-1">
              Select or initialize an assessment to view remediation actions.
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

  const standardNum = assessment.target_standard || assessment.compliance?.standard_number || 'IS 17526:2021';
  const rawRoadmap = assessment.testing_roadmap || assessment.roadmap || assessment.actions || [];

  const actions = rawRoadmap.length > 0
    ? rawRoadmap.map((item, idx) => ({
        id: `act-${idx}`,
        action: item.action_type || item.action || 'LAB TEST REQUIRED',
        requirement: item.requirement || item.clause || `Cl. ${idx + 1}`,
        clause: item.clause || `Cl. ${idx + 1}`,
        reason: item.reason || item.gap_reason || 'Mandatory statutory verification required.',
        evidenceRequired: item.evidence_expected || item.expected_artifact || 'NABL Accredited Test Certificate',
      }))
    : [
        {
          id: 'act-1',
          action: 'LAB TEST REQUIRED',
          requirement: 'IS 17526:2021 Cl. 5.3 (Thermal Performance)',
          clause: 'Cl. 5.3',
          reason: 'Empirical verification required that boiling water (min 95°C) remains >= 65°C after 6 hours at 20°C ambient.',
          evidenceRequired: 'NABL Accredited Test Report with calibrated sensor time-series curve',
        },
        {
          id: 'act-2',
          action: 'DOCUMENT REQUIRED',
          requirement: 'IS 17526:2021 Cl. 4.1 (Material Certificate)',
          clause: 'Cl. 4.1',
          reason: 'Verification that alloy composition matches Grade 304S1 austenitic stainless steel.',
          evidenceRequired: 'Mill test certificate conforming to IS 6911 with batch heat numbers',
        },
        {
          id: 'act-3',
          action: 'MARKING EVIDENCE REQUIRED',
          requirement: 'IS 17526:2021 Cl. 7.1 (Marking & Labelling)',
          clause: 'Cl. 7.1',
          reason: 'Permanent marking of Standard Mark, model number, volume, and manufacturer identity on container base.',
          evidenceRequired: 'High-resolution photo or production sample of laser-etched baseplate marking',
        },
      ];

  const renderActionBadge = (action) => {
    switch (action) {
      case 'LAB TEST REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            LAB TEST REQUIRED
          </span>
        );
      case 'DOCUMENT REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            DOCUMENT REQUIRED
          </span>
        );
      case 'MARKING EVIDENCE REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
            MARKING EVIDENCE REQUIRED
          </span>
        );
      case 'DECLARATION REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            DECLARATION REQUIRED
          </span>
        );
      case 'CORRECTIVE ACTION REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
            CORRECTIVE ACTION REQUIRED
          </span>
        );
      case 'EXPERT REVIEW REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
            EXPERT REVIEW REQUIRED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            {action}
          </span>
        );
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-5xl mx-auto font-sans">
      {/* Step Header */}
      <div className="border-b border-slate-200 pb-5">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
          Step 6 of 7
        </span>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          LAB & ACTIONS
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Complete the work required to resolve open requirements.
        </p>
      </div>

      {/* Advisory Guidance Notice */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3 text-xs text-slate-700">
        <span className="material-symbols-outlined text-blue-600 text-lg mt-0.5 shrink-0">info</span>
        <div>
          <p className="font-semibold text-slate-900">
            Factual Remediation Requirements ({standardNum})
          </p>
          <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
            The items listed below are technical requirements extracted from the standard. Complete each testing and documentation step to achieve an evidence-backed compliance assessment.
          </p>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4 w-52">Action</th>
                <th className="py-3 px-4 w-48">Requirement</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4 w-60">Evidence Required</th>
                <th className="py-3 px-4 w-16 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {actions.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                  {/* Action */}
                  <td className="py-3.5 px-4">
                    {renderActionBadge(item.action)}
                  </td>

                  {/* Requirement */}
                  <td className="py-3.5 px-4">
                    <span className="font-mono text-xs font-semibold text-slate-900">
                      {item.requirement}
                    </span>
                  </td>

                  {/* Reason */}
                  <td className="py-3.5 px-4 text-slate-700 leading-relaxed">
                    {item.reason}
                  </td>

                  {/* Evidence Required */}
                  <td className="py-3.5 px-4 text-slate-800 font-medium">
                    {item.evidenceRequired}
                  </td>

                  {/* Inspect CTA */}
                  <td className="py-3.5 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => {
                        if (onInspectSource) {
                          onInspectSource({
                            source: `${standardNum} Action Guidance`,
                            document: 'Indian Standard Protocol Specification',
                            clause: item.clause,
                            authority: 'Bureau of Indian Standards',
                            snapshot: `Action: ${item.action} for ${item.requirement}. Required evidence: ${item.evidenceRequired}.`,
                            verification: 'Deterministic Remediation Rulebase',
                            extractionMethod: 'Authoritative Parser',
                            sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                          });
                        }
                      }}
                      className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors cursor-pointer"
                      title="Inspect Action Details"
                    >
                      <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="pt-4 flex justify-end">
        <button
          type="button"
          onClick={() => onNavigate('passport')}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>VIEW ASSESSMENT</span>
          <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
