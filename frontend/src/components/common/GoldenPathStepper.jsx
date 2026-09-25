import React from 'react';

export const GOLDEN_PATH_STEPS = [
  { id: 'dna', step: '01', title: 'Product', stage: 'dna' },
  { id: 'applicability', step: '02', title: 'Applicability', stage: 'applicability' },
  { id: 'standards', step: '03', title: 'Requirements', stage: 'standards' },
  { id: 'evidence', step: '04', title: 'Evidence', stage: 'evidence' },
  { id: 'gaps', step: '05', title: 'Gaps', stage: 'gaps' },
  { id: 'lab', step: '06', title: 'Actions', stage: 'lab' },
  { id: 'passport', step: '07', title: 'Assessment', stage: 'passport' },
];

/**
 * GoldenPathStepper
 * 
 * Subtle, restrained workflow progress indicator:
 * Product -> Applicability -> Requirements -> Evidence -> Gaps -> Actions -> Assessment
 * 
 * Current step is highlighted. Future steps are muted. Previous steps are subtle.
 * Completed workflow stages do NOT use green (completion != compliance approval).
 */
export function GoldenPathStepper({
  activeTab,
  onSelectStep,
  assessment,
  onOpenTrustModal,
}) {
  // Determine current active step index (0-6)
  let currentStepIdx = 0;
  if (activeTab === 'dna' || activeTab === 'input') currentStepIdx = 0;
  else if (activeTab === 'applicability') currentStepIdx = 1;
  else if (activeTab === 'standards') currentStepIdx = 2;
  else if (activeTab === 'evidence') currentStepIdx = 3;
  else if (activeTab === 'gaps') currentStepIdx = 4;
  else if (activeTab === 'lab') currentStepIdx = 5;
  else if (activeTab === 'passport' || activeTab === 'reports') currentStepIdx = 6;
  else currentStepIdx = -1; // secondary view

  // Hide on entry or secondary views
  if (currentStepIdx === -1 || activeTab === 'entry') {
    return null;
  }

  const handlePrev = () => {
    if (currentStepIdx > 0) {
      onSelectStep(GOLDEN_PATH_STEPS[currentStepIdx - 1].stage);
    }
  };

  const handleNext = () => {
    if (currentStepIdx >= 0 && currentStepIdx < GOLDEN_PATH_STEPS.length - 1) {
      onSelectStep(GOLDEN_PATH_STEPS[currentStepIdx + 1].stage);
    }
  };

  return (
    <div className="bg-white border-b border-slate-200 px-4 sm:px-6 py-2.5 font-sans">
      <div className="flex items-center justify-between gap-4 max-w-7xl mx-auto">
        {/* Step Progression Indicators */}
        <nav aria-label="Workflow progress" className="flex items-center gap-1 sm:gap-2 overflow-x-auto py-0.5 no-scrollbar">
          {GOLDEN_PATH_STEPS.map((step, idx) => {
            const isActive = currentStepIdx === idx;
            const isPrevious = currentStepIdx > idx;
            const isFuture = currentStepIdx < idx;

            return (
              <React.Fragment key={step.id}>
                {idx > 0 && (
                  <span className={`text-[12px] px-0.5 select-none ${isPrevious ? 'text-slate-400' : 'text-slate-200'}`}>
                    &rarr;
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => onSelectStep(step.stage)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-all whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200 shadow-2xs'
                      : isPrevious
                      ? 'text-slate-700 hover:text-slate-900 hover:bg-slate-50 font-medium'
                      : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50 font-normal'
                  }`}
                >
                  <span className={`font-mono text-[10px] ${isActive ? 'text-blue-700 font-bold' : isPrevious ? 'text-slate-600 font-medium' : 'text-slate-300'}`}>
                    {step.step}
                  </span>
                  <span>{step.title}</span>
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        {/* Step Navigation Controls */}
        <div className="hidden sm:flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={handlePrev}
            disabled={currentStepIdx <= 0}
            className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-30 disabled:pointer-events-none rounded transition-colors cursor-pointer"
            title="Previous Step"
          >
            <span className="material-symbols-outlined text-[18px]">chevron_left</span>
          </button>
          <span className="text-[11px] font-mono text-slate-400">
            {currentStepIdx + 1} / {GOLDEN_PATH_STEPS.length}
          </span>
          <button
            type="button"
            onClick={handleNext}
            disabled={currentStepIdx >= GOLDEN_PATH_STEPS.length - 1}
            className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-100 disabled:opacity-30 disabled:pointer-events-none rounded transition-colors cursor-pointer"
            title="Next Step"
          >
            <span className="material-symbols-outlined text-[18px]">chevron_right</span>
          </button>
        </div>
      </div>
    </div>
  );
}
