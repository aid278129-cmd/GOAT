import React from 'react';

export function LabActionsView({ assessment, onNavigate }) {
  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">science</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Action Roadmap</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Select an assessment or enter product information in Step 1 to generate actionable testing and laboratory roadmaps.
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

  const roadmap = assessment.roadmap || assessment.actions || [];
  const primaryStandard = assessment.target_standard || (assessment.applicability?.[0]?.standard_number) || 'IS 17526:2021';

  // Fallback demo items if backend hasn't generated detailed roadmap
  const displayRoadmap = roadmap.length > 0 ? roadmap : [
    {
      action_type: 'LAB_TEST_REQUIRED',
      title: 'Thermal Retention 6-Hour Water Temperature Test',
      clause: 'IS 17526 Cl 5.4',
      priority: 'HIGH',
      reason: 'Mandatory statutory parameter under DPIIT QCO 2023. Missing accredited laboratory test certificate.',
      evidence_needed: 'NABL accredited test certificate showing water temperature >= 60 C after 6h.',
      suggested_step: 'Submit product test sample to recognized NABL testing facility.',
      target_labs: ['National Test House (NTH)', 'Shri Ram Institute for Industrial Research (SRI)'],
    },
    {
      action_type: 'LAB_TEST_REQUIRED',
      title: 'Inversion Hydrostatic Leakage Resistance Test',
      clause: 'IS 17526 Cl 5.2',
      priority: 'HIGH',
      reason: 'Physical leak-tightness test required under inversion at room temperature for 10 minutes.',
      evidence_needed: 'Lab test observation log confirming no fluid egress.',
      suggested_step: 'Conduct routine batch testing under Scheme of Testing and Inspection (STI).',
      target_labs: ['BIS Central Laboratory (Sahibabad)', 'ERTL / NABL Accredited Facilities'],
    },
    {
      action_type: 'PHOTO_MARKING_EVIDENCE_REQUIRED',
      title: 'Statutory ISI Mark & Registration Rating Plate',
      clause: 'IS 17526 Cl 7.1',
      priority: 'MEDIUM',
      reason: 'Mandatory rating plate labeling format required before customs clearance or domestic sale.',
      evidence_needed: 'High-resolution photograph of laser-etched / printed product bottom plate.',
      suggested_step: 'Upload engineering artwork or pre-production sample marking photograph.',
      target_labs: ['In-House Factory QA / BIS Officer Inspection'],
    },
  ];

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 07 / 08 &bull; Actionable Remediation Roadmap
            </span>
            <span className="text-xs text-slate-500">Target Testing Protocols & NABL Laboratory Alignment</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Laboratory Testing & Action Items</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Concrete remediation steps required to convert open gaps into verified compliance evidence under {primaryStandard}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('passport')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Compile Compliance Passport</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Action Disclaimer Notice */}
      <div className="p-3 bg-white border border-slate-200 rounded-lg text-xs text-slate-600 space-y-1 shadow-2xs">
        <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs">
          <span className="material-symbols-outlined text-sm text-indigo-600">info</span>
          <span>Pre-Certification Advisory Scope</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          Zyntrix provides actionable guidance for laboratory test parameters and documentation requirements. Zyntrix does not book laboratories, issue testing tokens, or communicate with the Bureau of Indian Standards on the manufacturer's behalf.
        </p>
      </div>

      {/* Action Items List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
            <span className="material-symbols-outlined text-slate-600 text-sm">checklist</span>
            <span>Remediation Tasks ({displayRoadmap.length})</span>
          </h2>
          <span className="text-[11px] font-mono text-slate-500">
            {displayRoadmap.filter((r) => r.priority === 'HIGH').length} High Priority
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {displayRoadmap.map((item, idx) => {
            const actionType = item.action_type || 'LAB_TEST_REQUIRED';
            const title = item.title || item.name || 'Testing Requirement';
            const clause = item.clause || item.clause_id || 'Standard Clause';
            const priority = item.priority || 'HIGH';
            const reason = item.reason || item.description || 'Mandatory parameter requiring proof of conformance.';
            const evidenceNeeded = item.evidence_needed || item.required_evidence || 'NABL test report';
            const suggestedStep = item.suggested_step || item.action || 'Submit sample for evaluation.';
            const targetLabs = item.target_labs || ['NABL Accredited Facilities'];

            return (
              <div
                key={idx}
                className="p-5 rounded-lg bg-white border border-slate-200 shadow-2xs space-y-4 hover:border-slate-300 transition"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-900 text-white">
                        {actionType}
                      </span>
                      <span className="text-xs font-mono font-semibold text-indigo-700">{clause}</span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">{title}</h3>
                  </div>

                  <div className="shrink-0">
                    {priority === 'HIGH' && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        HIGH PRIORITY
                      </span>
                    )}
                    {priority !== 'HIGH' && (
                      <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        {priority} PRIORITY
                      </span>
                    )}
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Defect & Reason:</span>
                    <p className="text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100 leading-relaxed font-sans">
                      {reason}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">Evidence Required:</span>
                    <p className="text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100 leading-relaxed font-mono text-[11px]">
                      {evidenceNeeded}
                    </p>
                  </div>
                </div>

                {/* Suggested Action & Labs */}
                <div className="p-3 rounded bg-indigo-50/50 border border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-mono uppercase text-indigo-900 font-bold">Suggested Immediate Step:</span>
                    <p className="text-indigo-950 font-medium">{suggestedStep}</p>
                  </div>
                  <div className="text-right sm:border-l sm:border-indigo-100 sm:pl-4 space-y-0.5">
                    <span className="text-[10px] font-mono uppercase text-indigo-800 font-bold">Target Test Facilities:</span>
                    <p className="text-indigo-900 font-mono text-[11px]">{targetLabs.join(' &bull; ')}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
