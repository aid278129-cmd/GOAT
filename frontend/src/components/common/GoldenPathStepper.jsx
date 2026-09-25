import React from 'react';

export const GOLDEN_PATH_STEPS = [
  { id: 'assistant', step: '01', title: 'BIS Assistant', icon: 'smart_toy', stage: 'assistant' },
  { id: 'dna', step: '02', title: 'Product DNA', icon: 'fingerprint', stage: 'dna' },
  { id: 'applicability', step: '03', title: 'BIS Applicability', icon: 'gavel', stage: 'applicability' },
  { id: 'standards', step: '04', title: 'Standards & Clauses', icon: 'menu_book', stage: 'standards' },
  { id: 'evidence', step: '05', title: 'Evidence Matrix', icon: 'policy', stage: 'evidence' },
  { id: 'gaps', step: '06', title: 'Compliance Gaps', icon: 'troubleshoot', stage: 'gaps' },
  { id: 'lab', step: '07', title: 'Lab & Actions', icon: 'science', stage: 'lab' },
  { id: 'passport', step: '08', title: 'Compliance Passport', icon: 'verified_user', stage: 'passport' },
];

export function GoldenPathStepper({
  activeTab,
  onSelectStep,
  assessment,
  onResetDemo,
  isResetting = false,
}) {
  // Determine current active step index (0-7)
  let currentStepIdx = 0;
  if (activeTab === 'assistant' || activeTab === 'input') currentStepIdx = 0;
  else if (activeTab === 'dna') currentStepIdx = 1;
  else if (activeTab === 'applicability') currentStepIdx = 2;
  else if (activeTab === 'standards') currentStepIdx = 3;
  else if (activeTab === 'evidence') currentStepIdx = 4;
  else if (activeTab === 'gaps') currentStepIdx = 5;
  else if (activeTab === 'lab') currentStepIdx = 6;
  else if (activeTab === 'passport' || activeTab === 'reports') currentStepIdx = 7;
  else currentStepIdx = -1; // secondary view like workstation, jobs, settings

  const productName = assessment?.product_name || assessment?.title || 'ThermoSteel Vacuum Flask 1000ml';
  const standardName = assessment?.target_standard || assessment?.compliance?.standard_number || 'IS 17526:2021';
  const assessmentNum = assessment?.assessment_number || (assessment?.assessment_id ? assessment.assessment_id.slice(0, 8) : 'SIH-DEMO');

  const handlePrev = () => {
    if (currentStepIdx > 0) {
      onSelectStep(GOLDEN_PATH_STEPS[currentStepIdx - 1].stage);
    }
  };

  const handleNext = () => {
    if (currentStepIdx >= 0 && currentStepIdx < GOLDEN_PATH_STEPS.length - 1) {
      onSelectStep(GOLDEN_PATH_STEPS[currentStepIdx + 1].stage);
    } else if (currentStepIdx === -1) {
      onSelectStep('assistant');
    }
  };

  return (
    <div className="bg-white border-b border-[#E2E8F0] shadow-xs">
      {/* Top Bar Context & Actions */}
      <div className="px-4 sm:px-6 py-2 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-200 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse"></span>
            Golden Path Workflow
          </span>
          <span className="font-semibold text-slate-800 truncate max-w-xs sm:max-w-md">
            {productName}
          </span>
          <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
            {standardName}
          </span>
          <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
            0% LLM Authority
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onResetDemo && (
            <button
              type="button"
              onClick={onResetDemo}
              disabled={isResetting}
              className="px-2.5 py-1 text-[11px] font-semibold text-indigo-700 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-50"
              title="Reset the deterministic Golden SIH Demo Assessment"
            >
              <span className={`material-symbols-outlined text-[13px] ${isResetting ? 'animate-spin' : ''}`}>
                refresh
              </span>
              <span>{isResetting ? 'Resetting...' : 'Reset Golden Demo'}</span>
            </button>
          )}

          {currentStepIdx >= 0 && (
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentStepIdx === 0}
                className="px-2 py-1 text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 disabled:opacity-40 rounded border border-slate-200 transition-colors flex items-center gap-0.5 cursor-pointer"
                title="Previous Golden Path Step"
              >
                <span className="material-symbols-outlined text-[13px]">arrow_back</span>
                <span className="hidden sm:inline">Prev</span>
              </button>
              <button
                type="button"
                onClick={handleNext}
                disabled={currentStepIdx === GOLDEN_PATH_STEPS.length - 1}
                className="px-2.5 py-1 text-[11px] font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 rounded transition-colors flex items-center gap-0.5 cursor-pointer shadow-2xs"
                title="Next Golden Path Step"
              >
                <span className="hidden sm:inline">Next</span>
                <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 8-Stage Interactive Track */}
      <div className="px-4 sm:px-6 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-1 py-1.5 min-w-max">
          {GOLDEN_PATH_STEPS.map((s, idx) => {
            const isActive = currentStepIdx === idx;
            const isCompleted = currentStepIdx > idx;

            return (
              <React.Fragment key={s.id}>
                <button
                  type="button"
                  onClick={() => onSelectStep(s.stage)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all cursor-pointer ${
                    isActive
                      ? 'bg-indigo-600 text-white font-bold shadow-xs'
                      : isCompleted
                      ? 'bg-slate-100 text-slate-800 hover:bg-slate-200 font-medium'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[15px] ${
                      isActive ? 'text-white' : isCompleted ? 'text-indigo-600' : 'text-slate-400'
                    }`}
                  >
                    {isCompleted ? 'check_circle' : s.icon}
                  </span>
                  <span className="font-mono text-[10px] opacity-75">{s.step}</span>
                  <span className="whitespace-nowrap">{s.title}</span>
                </button>

                {idx < GOLDEN_PATH_STEPS.length - 1 && (
                  <span
                    className={`material-symbols-outlined text-[14px] shrink-0 ${
                      currentStepIdx > idx ? 'text-indigo-400' : 'text-slate-300'
                    }`}
                  >
                    chevron_right
                  </span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
