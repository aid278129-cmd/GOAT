import React, { useState } from 'react';

export const GOLDEN_PATH_STEPS = [
  { id: 'assistant', step: '01', title: 'BIS Assistant', subtitle: 'Workflow Entry', icon: 'smart_toy', stage: 'assistant' },
  { id: 'dna', step: '02', title: 'Product DNA', subtitle: 'Fact Ledger', icon: 'fingerprint', stage: 'dna' },
  { id: 'applicability', step: '03', title: 'BIS Applicability', subtitle: 'Statutory Scoping', icon: 'gavel', stage: 'applicability' },
  { id: 'standards', step: '04', title: 'Standards & Clauses', subtitle: 'Requirement Trace', icon: 'menu_book', stage: 'standards' },
  { id: 'evidence', step: '05', title: 'Evidence Matrix', subtitle: 'Trust Boundaries', icon: 'policy', stage: 'evidence' },
  { id: 'gaps', step: '06', title: 'Compliance Gaps', subtitle: 'Gap Ledger', icon: 'troubleshoot', stage: 'gaps' },
  { id: 'lab', step: '07', title: 'Lab & Actions', subtitle: 'Remediation Roadmap', icon: 'science', stage: 'lab' },
  { id: 'passport', step: '08', title: 'Compliance Passport', subtitle: 'Auditable Artifact', icon: 'verified_user', stage: 'passport' },
];

export function GoldenPathStepper({
  activeTab,
  onSelectStep,
  assessment,
  onResetDemo,
  isResetting = false,
}) {
  const [showTrustModal, setShowTrustModal] = useState(false);

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
  const hasAssessment = Boolean(assessment);

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

  const [trustModalTab, setTrustModalTab] = useState('authority'); // 'authority' | 'jury_qa' | 'manifest'

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
          <span className="font-mono text-[11px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
            {standardName}
          </span>
          <button
            type="button"
            onClick={() => setShowTrustModal(true)}
            className="font-mono text-[10px] text-indigo-700 hover:text-indigo-900 bg-indigo-50/80 hover:bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200 transition-colors flex items-center gap-1 cursor-pointer"
            title="Inspect how compliance results are determined and review Jury Q&A"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>0% LLM Authority &bull; Jury Readiness & FAQ</span>
            <span className="material-symbols-outlined text-[12px]">info</span>
          </button>
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
            const isBlocked = !hasAssessment && idx > 0 && currentStepIdx !== idx;

            return (
              <React.Fragment key={s.id}>
                <button
                  type="button"
                  onClick={() => onSelectStep(s.stage)}
                  disabled={isBlocked}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all cursor-pointer ${
                    isActive
                      ? 'bg-indigo-600 text-white font-bold shadow-xs'
                      : isCompleted
                      ? 'bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium'
                      : isBlocked
                      ? 'text-slate-300 cursor-not-allowed'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                  }`}
                  title={`${s.step}: ${s.title} — ${s.subtitle}`}
                >
                  <span
                    className={`material-symbols-outlined text-[15px] ${
                      isActive ? 'text-white' : isCompleted ? 'text-slate-600' : isBlocked ? 'text-slate-300' : 'text-slate-400'
                    }`}
                  >
                    {isCompleted ? 'check' : s.icon}
                  </span>
                  <span className="font-mono text-[10px] opacity-75">{s.step}</span>
                  <span className="whitespace-nowrap">{s.title}</span>
                </button>

                {idx < GOLDEN_PATH_STEPS.length - 1 && (
                  <span
                    className={`material-symbols-outlined text-[14px] shrink-0 ${
                      currentStepIdx > idx ? 'text-slate-400' : 'text-slate-300'
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

      {/* Trust & Transparency Panel Modal */}
      {showTrustModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-3xl w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700">
                  <span className="material-symbols-outlined text-lg">balance</span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Trust, Authority Boundary & Jury Readiness</h3>
                  <p className="text-xs text-slate-500">Zyntrix Architectural Authority, 10 Jury Questions & Corpus Manifest</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowTrustModal(false)}
                className="p-1 text-slate-400 hover:text-slate-700 rounded transition cursor-pointer"
              >
                <span className="material-symbols-outlined text-base">close</span>
              </button>
            </div>

            {/* Modal Sub-Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-mono">
              <button
                type="button"
                onClick={() => setTrustModalTab('authority')}
                className={`flex-1 py-1.5 rounded-md font-bold transition text-center cursor-pointer ${
                  trustModalTab === 'authority' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                1. Authority Boundary (0% AI)
              </button>
              <button
                type="button"
                onClick={() => setTrustModalTab('jury_qa')}
                className={`flex-1 py-1.5 rounded-md font-bold transition text-center cursor-pointer ${
                  trustModalTab === 'jury_qa' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                2. Jury Questions (Q1-Q10)
              </button>
              <button
                type="button"
                onClick={() => setTrustModalTab('manifest')}
                className={`flex-1 py-1.5 rounded-md font-bold transition text-center cursor-pointer ${
                  trustModalTab === 'manifest' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                3. Corpus Coverage Manifest
              </button>
            </div>

            {/* Scrollable Tab Body */}
            <div className="overflow-y-auto flex-1 pr-1 space-y-4">
              {trustModalTab === 'authority' && (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* AI Assists */}
                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-indigo-600">psychology</span>
                        <span className="font-bold text-slate-900 uppercase font-mono text-[10px] tracking-wider">
                          AI Assists With (0% Authority)
                        </span>
                      </div>
                      <ul className="space-y-1.5 text-slate-600">
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-500 font-bold">&bull;</span>
                          <span>Natural language understanding & multilingual user inquiry</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-500 font-bold">&bull;</span>
                          <span>Technical attribute extraction proposals from product artifacts</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-500 font-bold">&bull;</span>
                          <span>Candidate standard identification for deterministic evaluation</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-500 font-bold">&bull;</span>
                          <span>Interactive explanation and remediation assistance</span>
                        </li>
                      </ul>
                    </div>

                    {/* Deterministic Systems */}
                    <div className="p-3.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-indigo-700">verified</span>
                        <span className="font-bold text-indigo-900 uppercase font-mono text-[10px] tracking-wider">
                          Deterministic Systems Determine (100%)
                        </span>
                      </div>
                      <ul className="space-y-1.5 text-indigo-950">
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-700 font-bold">&bull;</span>
                          <span>Standard applicability & official Gazette QCO mandate status</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-700 font-bold">&bull;</span>
                          <span>Evidence class eligibility & SHA-256 integrity verification</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-700 font-bold">&bull;</span>
                          <span>Clause requirement satisfaction against statutory tolerances</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <span className="text-indigo-700 font-bold">&bull;</span>
                          <span>Compliance gap ledger & cryptographic passport provenance</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-900 space-y-1">
                    <div className="font-bold flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-amber-700">shield</span>
                      <span>Safe Abstention Invariant</span>
                    </div>
                    <p className="leading-relaxed text-amber-800">
                      If authoritative Gazette text or verified laboratory evidence is unavailable, the compiler abstains with explicit <strong>MISSING_EVIDENCE</strong>. The system never hallucinates compliance or certification.
                    </p>
                  </div>
                </div>
              )}

              {trustModalTab === 'jury_qa' && (
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 space-y-1">
                    <div className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-indigo-600">help</span>
                      <span>Q1: What makes this different from BIS search?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      BIS search helps locate standards and regulatory information. Zyntrix compiles a product artifact into Product DNA, determines applicable requirements, maps evidence to requirements, identifies evidence gaps, and produces a traceable pre-certification assessment.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-slate-600">database</span>
                      <span>Q2: Where does the data come from?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      From official regulatory sources: Gazette of India notifications, DPIIT QCO orders, BIS Manakonline catalog schedules, and recognized laboratory rosters. Full technical clause specifications require authorized manual procurement. Synthetic controlled fixtures are strictly segregated and flagged as non-authoritative.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 space-y-1">
                    <div className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-indigo-600">gavel</span>
                      <span>Q3: Does the LLM decide compliance?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      No. AI assists with interaction, extraction, and candidate interpretation (0% compliance authority). Deterministic engines govern applicability, evidence eligibility, requirement evaluation, gap aggregation, and passport integrity.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-amber-600">shield</span>
                      <span>Q4: What happens if the system does not know?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      It abstains and exposes the missing, unverified, or acquisition-pending state instead of inventing a regulatory conclusion.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 space-y-1">
                    <div className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-indigo-600">science</span>
                      <span>Q5: Can a manufacturer datasheet satisfy a laboratory test?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      No. Evidence eligibility is requirement-specific. Empirical laboratory requirements require appropriate test evidence from recognized accredited laboratories.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-rose-600">verified_user</span>
                      <span>Q6: Is this a BIS certificate?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      No. The output is an evidence-backed pre-certification compliance assessment. It is not BIS certification.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 space-y-1">
                    <div className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-indigo-600">security</span>
                      <span>Q7: How do you prevent hallucinated compliance?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      Compliance authority is outside the LLM. Claims must pass through source, applicability, evidence, requirement, and deterministic evaluation controls.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-purple-600">alt_route</span>
                      <span>Q8: What happens when evidence conflicts?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      The conflicting evidence is quarantined and routed for expert review rather than automatically selecting one value.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 space-y-1">
                    <div className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-indigo-600">update</span>
                      <span>Q9: How do standards/QCO changes get handled?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      Through versioned regulatory catalogs and SHA-256 change detection in the repository manifest. When a standard or QCO is amended, existing assessments retain their immutable point-in-time snapshot.
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                    <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-emerald-600">inventory_2</span>
                      <span>Q10: What is the current corpus coverage?</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed font-sans">
                      The verified repository manifest contains 51 standard records, 49 DPIIT QCO orders, 52 document records (including 46 acquired regulatory records, 6 acquisition-pending full standards, 1 verified benchmark clause set, and 1 segregated synthetic test fixture).
                    </p>
                  </div>
                </div>
              )}

              {trustModalTab === 'manifest' && (
                <div className="space-y-4 text-xs font-mono">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                      <span className="text-[10px] uppercase text-slate-400 font-bold block">Standards Records</span>
                      <div className="text-xl font-bold text-slate-900 mt-1">51</div>
                      <span className="text-[10px] text-slate-500">BIS ManakOnline Catalog</span>
                    </div>

                    <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                      <span className="text-[10px] uppercase text-purple-700 font-bold block">QCO Orders</span>
                      <div className="text-xl font-bold text-purple-900 mt-1">49</div>
                      <span className="text-[10px] text-purple-700">Official Gazette Verified</span>
                    </div>

                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                      <span className="text-[10px] uppercase text-emerald-700 font-bold block">Regulatory Records</span>
                      <div className="text-xl font-bold text-emerald-900 mt-1">46</div>
                      <span className="text-[10px] text-emerald-700">Acquired & Grounded</span>
                    </div>

                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <span className="text-[10px] uppercase text-amber-700 font-bold block">Acquisition Pending</span>
                      <div className="text-xl font-bold text-amber-900 mt-1">6</div>
                      <span className="text-[10px] text-amber-700">Requires Procurement</span>
                    </div>

                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <span className="text-[10px] uppercase text-blue-700 font-bold block">Synthetic Fixture</span>
                      <div className="text-xl font-bold text-blue-900 mt-1">1</div>
                      <span className="text-[10px] text-blue-700">FIX-IS17526 Segregated</span>
                    </div>

                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                      <span className="text-[10px] uppercase text-slate-400 font-bold block">Blocked Domains</span>
                      <div className="text-xl font-bold text-slate-900 mt-1">0</div>
                      <span className="text-[10px] text-slate-500">Zero Scraped Sources</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5 text-[11px]">
                    <div className="font-bold text-slate-900 uppercase">Cryptographic Source Integrity Hash:</div>
                    <code className="text-slate-700 bg-white p-2 rounded border border-slate-200 block text-[10px] break-all">
                      SHA-256: 86a14e17b5709d84d168228990d1176ac9e1fb1491aff8e07cdca85cbb97ddb0
                    </code>
                    <p className="text-slate-500 text-[10px] font-sans pt-1">
                      Corpus manifest dynamically verified under Milestone M22/M25.3 data governance policy. Full BIS technical standards require authorized purchase from BIS.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowTrustModal(false)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
