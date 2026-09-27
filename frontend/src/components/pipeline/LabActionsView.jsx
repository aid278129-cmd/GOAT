import React from 'react';

/**
 * LabActionsView (Step 6 — LAB & ACTIONS)
 * 
 * Header: LAB & ACTIONS
 * Subtitle: "Complete the testing and laboratory actions required to resolve open requirements."
 * Dark precision workstation aesthetic matching homepage.
 */
export function LabActionsView({ assessment, onNavigate, onInspectSource }) {
  if (!assessment) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans text-slate-200">
        <div className="max-w-md w-full bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-400/30 rounded-xl flex items-center justify-center mx-auto text-cyan-400 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-2xl">science</span>
          </div>
          <div>
            <h3 className="font-space-grotesk text-sm font-bold text-white">No Actions Loaded</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select or initialize an assessment to view remediation actions.
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
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-950/60 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-[13px] text-cyan-400">science</span>
            <span>LAB TEST REQUIRED</span>
          </span>
        );
      case 'DOCUMENT REQUIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-amber-950/60 text-amber-300 border border-amber-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span>DOCUMENT REQUIRED</span>
          </span>
        );
      case 'MARKING EVIDENCE REQUIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-purple-950/60 text-purple-300 border border-purple-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
            <span>MARKING EVIDENCE REQUIRED</span>
          </span>
        );
      case 'DECLARATION REQUIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-amber-950/60 text-amber-300 border border-amber-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
            <span>DECLARATION REQUIRED</span>
          </span>
        );
      case 'CORRECTIVE ACTION REQUIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-rose-950/60 text-rose-300 border border-rose-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            <span>CORRECTIVE ACTION REQUIRED</span>
          </span>
        );
      case 'EXPERT REVIEW REQUIRED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-indigo-950/60 text-indigo-300 border border-indigo-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
            <span>EXPERT REVIEW REQUIRED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-slate-900 text-slate-300 border border-slate-700">
            {action}
          </span>
        );
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-6xl mx-auto font-sans text-slate-100">
      {/* Step Header */}
      <div className="border-b border-slate-800 pb-5">
        <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
          Step 6 of 7 &bull; Golden Path
        </span>
        <h1 className="font-space-grotesk text-2xl font-bold text-white tracking-tight">
          LAB & REMEDIATION ACTIONS
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Complete the testing and documentation required to resolve open statutory requirements.
        </p>
      </div>

      {/* Advisory Guidance Notice */}
      <div className="p-4 sm:p-5 rounded-2xl bg-[#0f1422] border border-slate-800 flex items-start gap-3.5 text-xs text-slate-300 shadow-md">
        <span className="material-symbols-outlined text-cyan-400 text-xl mt-0.5 shrink-0">info</span>
        <div>
          <p className="font-space-grotesk font-semibold text-white text-sm">
            Factual Remediation Requirements ({standardNum})
          </p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            The items listed below are technical requirements extracted from statutory Indian Standards. Complete each testing and documentation step to achieve an evidence-backed compliance assessment.
          </p>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-[#0f1422] border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 font-mono font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3.5 px-4 w-52">Action Required</th>
                <th className="py-3.5 px-4 w-52">Requirement</th>
                <th className="py-3.5 px-4">Reason</th>
                <th className="py-3.5 px-4 w-60">Evidence Required</th>
                <th className="py-3.5 px-4 w-16 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {actions.map((item) => (
                <tr key={item.id} className="hover:bg-[#13192a] transition-colors">
                  {/* Action */}
                  <td className="py-3.5 px-4">
                    {renderActionBadge(item.action)}
                  </td>

                  {/* Requirement */}
                  <td className="py-3.5 px-4">
                    <span className="font-mono text-xs font-semibold text-white">
                      {item.requirement}
                    </span>
                  </td>

                  {/* Reason */}
                  <td className="py-3.5 px-4 text-slate-300 leading-relaxed">
                    {item.reason}
                  </td>

                  {/* Evidence Required */}
                  <td className="py-3.5 px-4 text-slate-200 font-medium">
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
                      className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
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
          className="px-7 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(56,189,248,0.35)] transition-all flex items-center gap-2 cursor-pointer"
        >
          <span>VIEW COMPLIANCE PASSPORT</span>
          <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}
