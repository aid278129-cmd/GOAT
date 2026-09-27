import React from 'react';

export const GOLDEN_PATH_STEPS = [
  { id: 'dna', step: '01', title: 'Product DNA', stage: 'dna' },
  { id: 'applicability', step: '02', title: 'Applicability', stage: 'applicability' },
  { id: 'standards', step: '03', title: 'Requirements', stage: 'standards' },
  { id: 'evidence', step: '04', title: 'Evidence Matrix', stage: 'evidence' },
  { id: 'gaps', step: '05', title: 'Gap Engine', stage: 'gaps' },
  { id: 'lab', step: '06', title: 'Lab Dispatch', stage: 'lab' },
  { id: 'passport', step: '07', title: 'Passport', stage: 'passport' },
];

/**
 * GoldenPathStepper
 * 
 * Subtle, restrained workflow progress indicator:
 * Product -> Applicability -> Requirements -> Evidence -> Gaps -> Actions -> Assessment
 * 
 * Dark precision workstation styling matching homepage.
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
    <div className="bg-[#0b0f19] border-b border-slate-800/80 px-4 sm:px-6 py-2 font-sans">
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
                  <span className={`text-[12px] px-0.5 select-none ${isPrevious ? 'text-cyan-500/60' : 'text-slate-700'}`}>
                    &rarr;
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => onSelectStep(step.stage)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-all whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-500/40 shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                      : isPrevious
                      ? 'text-slate-300 hover:text-cyan-200 hover:bg-slate-800/60 font-medium'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 font-normal'
                  }`}
                >
                  <span className={`font-mono text-[10px] ${isActive ? 'text-cyan-400 font-bold' : isPrevious ? 'text-cyan-500/80 font-medium' : 'text-slate-600'}`}>
                    {step.step}
                  </span>
                  <span>{step.title}</span>
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        {/* Step Navigation Controls & Trust Modal Button */}
        <div className="hidden sm:flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={onOpenTrustModal}
            className="flex items-center gap-1 text-[11px] font-mono text-cyan-400/80 hover:text-cyan-300 bg-cyan-950/30 hover:bg-cyan-950/50 border border-cyan-500/20 px-2 py-0.5 rounded cursor-pointer transition-colors"
            title="Inspect 9-Layer Regulatory Trust Architecture"
          >
            <span className="material-symbols-outlined text-[13px]">shield</span>
            <span>Trust Architecture</span>
          </button>

          <div className="h-3 w-px bg-slate-800" />

          <button
            type="button"
            onClick={handlePrev}
            disabled={currentStepIdx <= 0}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-20 disabled:pointer-events-none rounded transition-colors cursor-pointer"
            title="Previous Step"
          >
            <span className="material-symbols-outlined text-[16px]">chevron_left</span>
          </button>
          <button
            type="button"
            onClick={handleNext}
            disabled={currentStepIdx >= GOLDEN_PATH_STEPS.length - 1}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-20 disabled:pointer-events-none rounded transition-colors cursor-pointer"
            title="Next Step"
          >
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          </button>
        </div>
      </div>
    </div>
  );
}
