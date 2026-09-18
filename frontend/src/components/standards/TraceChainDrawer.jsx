import React, { useState } from 'react';
import {
  ASSESSMENT_STATE_CONFIG,
  EngineeringAssessmentState,
} from '../../types/standardsTypes';

export function TraceChainDrawer({ isOpen, onClose, result, requirement, onSpatialInspect }) {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedTrace, setCopiedTrace] = useState(false);

  if (!isOpen || !result) return null;

  const { traceChain, auditRecord, engineeringResult, explanation, assessmentId, timestamp } = result;
  const stateConfig = ASSESSMENT_STATE_CONFIG[engineeringResult] || ASSESSMENT_STATE_CONFIG[EngineeringAssessmentState.NOT_ASSESSED];

  const handleCopyHash = (hash) => {
    if (!hash) return;
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyTrace = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopiedTrace(true);
    setTimeout(() => setCopiedTrace(false), 2000);
  };

  const isSpatialApplicable =
    requirement?.requiredParameterKey?.includes('creepage') ||
    requirement?.requiredParameterKey?.includes('clearance') ||
    requirement?.requiredParameterKey?.includes('dimension') ||
    requirement?.requirementType === 'MECHANICAL';

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/60 backdrop-blur-xs animate-fadeIn font-sans">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-slideLeft">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <span className="material-symbols-outlined text-lg">timeline</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider font-mono">
                  Traceability Chain
                </h2>
                <span className="font-mono text-[10px] text-slate-500 bg-white border border-slate-200 px-1.5 py-0.5 rounded">
                  {assessmentId}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Complete verifiable audit trace from standard to deterministic engineering result
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Engineering Assessment State Banner */}
          <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${stateConfig.badge}`}>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-2xl">{stateConfig.icon}</span>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest font-bold opacity-75">
                  ENGINEERING ASSESSMENT (DETERMINISTIC)
                </div>
                <div className="text-sm font-bold">{stateConfig.label}</div>
              </div>
            </div>
            <div className="text-[11px] font-mono opacity-80 text-right">
              {new Date(timestamp).toLocaleString()}
            </div>
          </div>

          {/* Regulatory Mandate Warning */}
          <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs text-amber-900 leading-relaxed flex items-start gap-2">
            <span className="material-symbols-outlined text-sm text-amber-600 shrink-0 mt-0.5">shield</span>
            <div>
              <span className="font-bold">Regulatory Separation Notice:</span> This output represents an internal{' '}
              <span className="font-semibold">ENGINEERING ASSESSMENT</span> derived deterministically from accepted evidence and Product DNA. It does NOT constitute BIS Certification, Laboratory Certification, or Statutory Attestation.
            </div>
          </div>

          {/* Question: Why did Zyntrix produce this result? */}
          <div className="p-3.5 bg-blue-50/50 border border-blue-200 rounded-lg">
            <div className="text-[11px] font-mono font-bold text-blue-900 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-blue-600">help</span>
              Why did Zyntrix produce this result?
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-sans">{explanation}</p>
          </div>

          {/* Trace Chain Stepper */}
          <div className="space-y-3">
            <div className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Step-by-Step Statutory Provenance Chain
            </div>

            <div className="relative border-l-2 border-blue-200 ml-3.5 pl-6 space-y-6">
              {/* Step 1: Standard */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  1
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">Statutory Standard</div>
                <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">
                  {traceChain?.standard?.identifier} — {traceChain?.standard?.revisionYear}
                </div>
                <div className="text-xs text-slate-600 mt-0.5">{traceChain?.standard?.title}</div>
              </div>

              {/* Step 2: Clause Reference */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  2
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">Statutory Clause & Sub-Clause</div>
                <div className="text-xs font-bold text-slate-900 font-mono mt-0.5">
                  {traceChain?.clause?.clauseRef} {traceChain?.clause?.subClause && `(${traceChain.clause.subClause})`}
                </div>
                <div className="text-[11px] text-slate-500">
                  {traceChain?.clause?.part} &gt; {traceChain?.clause?.section}
                </div>
              </div>

              {/* Step 3: Requirement Definition & Rule */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  3
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">
                  Requirement & Comparison Rule
                </div>
                <div className="text-xs font-mono text-slate-700 bg-slate-50 border border-slate-200 p-2 rounded mt-1">
                  ID: <span className="font-bold">{traceChain?.requirement?.reqId}</span> | Operator:{' '}
                  <span className="font-bold text-blue-700">{traceChain?.requirement?.comparisonType}</span>
                  {traceChain?.requirement?.targetValue && (
                    <span> | Target: {traceChain.requirement.targetValue} {traceChain.requirement.unit || ''}</span>
                  )}
                  {traceChain?.requirement?.minValue && (
                    <span> | Range: [{traceChain.requirement.minValue} - {traceChain.requirement.maxValue} {traceChain.requirement.unit || ''}]</span>
                  )}
                </div>
                <div className="text-xs text-slate-600 mt-1">{traceChain?.requirement?.text}</div>
              </div>

              {/* Step 4: Verified Product DNA Parameter */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  4
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">Product DNA Parameter</div>
                {traceChain?.productDna ? (
                  <div className="p-2.5 bg-emerald-50/60 border border-emerald-200 rounded mt-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-emerald-900">
                        {traceChain.productDna.key}: {traceChain.productDna.value} {traceChain.productDna.unit || ''}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-300">
                        {traceChain.productDna.reviewStatus}
                      </span>
                    </div>
                    {traceChain.productDna.locationCitation && (
                      <div className="text-[11px] text-slate-600 mt-1">
                        Citation: {traceChain.productDna.locationCitation}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-2 bg-amber-50 border border-amber-200 rounded mt-1 text-xs text-amber-800">
                    No matching parameter in Product DNA repository.
                  </div>
                )}
              </div>

              {/* Step 5 & 6: Evidence & SHA-256 Hash */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  5
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">Accepted Source Evidence</div>
                {traceChain?.evidence ? (
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded mt-1 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-slate-900">{traceChain.evidence.id}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800">
                        {traceChain.evidence.acceptanceStatus}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-600 truncate">{traceChain.evidence.fileName}</div>
                    <div className="flex items-center gap-1 font-mono text-[10px] text-slate-500 bg-white p-1 rounded border border-slate-200">
                      <span className="truncate">{traceChain.evidence.sha256Hash}</span>
                      <button
                        type="button"
                        onClick={() => handleCopyHash(traceChain.evidence.sha256Hash)}
                        className="text-slate-400 hover:text-slate-700 shrink-0 cursor-pointer"
                        title="Copy SHA-256 Hash"
                      >
                        <span className="material-symbols-outlined text-xs">
                          {copiedHash ? 'check' : 'content_copy'}
                        </span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-2 bg-slate-100 border border-slate-200 rounded mt-1 text-xs text-slate-500">
                    No accepted evidence artifact attached.
                  </div>
                )}
              </div>

              {/* Step 6: Deterministic Rule Calculation */}
              <div className="relative group">
                <div className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-white flex items-center justify-center text-white text-[8px] font-bold">
                  6
                </div>
                <div className="text-[10px] font-mono text-slate-500 uppercase font-bold">Deterministic Mathematical Evaluation</div>
                <div className="text-xs text-slate-800 mt-1 font-mono bg-slate-50 border border-slate-200 p-2 rounded">
                  {explanation}
                </div>
              </div>
            </div>
          </div>

          {/* Real Backend Engine Execution Trace */}
          {result.trace_chain && Array.isArray(result.trace_chain) && result.trace_chain.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-sm text-blue-600">terminal</span>
                  Backend Deterministic Engine Execution Steps ({result.trace_chain.length})
                </span>
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                  PostgreSQL Verified
                </span>
              </div>

              <div className="space-y-2">
                {result.trace_chain.map((step, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-[10px] flex items-center justify-center font-mono">
                          {step.step_number || idx + 1}
                        </span>
                        <span className="font-bold text-slate-800 font-mono text-[11px]">{step.title}</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        step.status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' :
                        step.status === 'GAP' || step.status === 'FAILED' ? 'bg-rose-100 text-rose-800' :
                        step.status === 'TERMINATED' ? 'bg-slate-200 text-slate-700' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {step.status}
                      </span>
                    </div>
                    <p className="text-slate-600 pl-7">{step.description}</p>
                    {step.metadata && Object.keys(step.metadata).length > 0 && (
                      <div className="ml-7 mt-1.5 p-2 bg-white rounded border border-slate-200 text-[10px] font-mono text-slate-600 space-y-0.5">
                        {Object.entries(step.metadata).map(([k, v]) => (
                          <div key={k} className="flex items-center justify-between truncate">
                            <span className="text-slate-400">{k}:</span>
                            <span className="text-slate-800 font-semibold truncate ml-2">
                              {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Spatial CAD Action if Applicable */}
          {isSpatialApplicable && onSpatialInspect && (
            <div className="p-3 bg-indigo-50/50 border border-indigo-200 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-indigo-950">
                <span className="material-symbols-outlined text-indigo-600">view_in_ar</span>
                <span>Spatial CAD dimension verification available on Digital Twin</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  onSpatialInspect(requirement);
                  onClose();
                }}
                className="px-2.5 py-1 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded transition cursor-pointer"
              >
                Inspect in 3D CAD Twin
              </button>
            </div>
          )}

          {/* Immutable Audit Ledger Record */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
            <div className="text-[11px] font-mono font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-slate-500">receipt_long</span>
                Immutable Assessment Audit Record
              </span>
              <button
                type="button"
                onClick={handleCopyTrace}
                className="text-[10px] font-mono text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer"
              >
                <span className="material-symbols-outlined text-xs">
                  {copiedTrace ? 'check' : 'content_copy'}
                </span>
                {copiedTrace ? 'Copied' : 'Copy Audit JSON'}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-600">
              <div>Assessment ID: <span className="text-slate-900 font-bold">{auditRecord?.assessmentId}</span></div>
              <div>Execution: <span className="text-slate-900 font-bold">{auditRecord?.executionStatus}</span></div>
              <div>Rule Version: <span className="text-slate-900 font-bold">{auditRecord?.ruleVersion}</span></div>
              <div>Knowledge Base: <span className="text-slate-900 font-bold">{auditRecord?.knowledgeBaseVersion}</span></div>
              <div className="col-span-2 truncate">
                Evidence Hash: <span className="text-slate-900">{auditRecord?.evidenceHashes?.[0]}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <span className="font-mono text-[10px] text-slate-400">
            Zyntrix Deterministic Compiler • Non-destructive Evaluation
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 rounded-md transition"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
}
