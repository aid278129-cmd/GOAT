import React, { useState } from 'react';
import { truncateHash } from '../../utils/evidenceCrypto';

export function ConflictResolutionModal({ conflict, isOpen, onClose, onResolve }) {
  const [selectedChoice, setSelectedChoice] = useState('candidateA');
  const [customValue, setCustomValue] = useState('');
  const [rationale, setRationale] = useState('');
  const [error, setError] = useState(null);

  if (!isOpen || !conflict) return null;

  const handleResolveSubmit = (e) => {
    e.preventDefault();
    if (!rationale.trim()) {
      setError('Mandatory resolution rationale is required for regulatory traceability.');
      return;
    }

    let finalValue = conflict.candidateA.value;
    if (selectedChoice === 'candidateB') {
      finalValue = conflict.candidateB.value;
    } else if (selectedChoice === 'custom') {
      if (!customValue.trim()) {
        setError('Please provide a reconciled value.');
        return;
      }
      finalValue = customValue.trim();
    }

    onResolve({
      conflictId: conflict.conflictId,
      resolvedValue: finalValue,
      selectedCandidateKey: selectedChoice,
      rationale: rationale.trim(),
    });

    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[#0d121f] text-slate-100 border border-slate-800 rounded-2xl max-w-2xl w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-amber-950/30">
          <div className="flex items-center gap-2.5">
            <span className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-800/80 text-amber-400 flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-base">warning</span>
            </span>
            <div>
              <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">
                Parameter Conflict Resolution
              </h3>
              <span className="text-[10px] font-mono text-amber-400 font-semibold block tracking-wider uppercase">
                MANDATORY HUMAN ENGINEERING REVIEW // AUDITABLE RESOLUTION
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleResolveSubmit} className="p-6 flex flex-col gap-5 overflow-y-auto">
          <div>
            <span className="text-xs text-slate-400 block font-mono">Discrepancy Detected for:</span>
            <h4 className="text-base font-bold text-slate-100 font-['Space_Grotesk'] mt-0.5">{conflict.parameterName}</h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Two accepted evidence artifacts specify differing values. Under regulatory integrity rules, the system will not automatically select a value. Affirmative engineering resolution is required.
            </p>
          </div>

          {/* Side-by-Side Candidates */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Candidate A */}
            <div
              onClick={() => setSelectedChoice('candidateA')}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                selectedChoice === 'candidateA'
                  ? 'border-cyan-400 bg-cyan-950/40 shadow-inner'
                  : 'border-slate-800 bg-slate-900/60 hover:bg-slate-900/90'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-cyan-300">
                  Candidate A
                </span>
                <input
                  type="radio"
                  name="candidateChoice"
                  checked={selectedChoice === 'candidateA'}
                  onChange={() => setSelectedChoice('candidateA')}
                  className="text-cyan-500 focus:ring-cyan-500"
                />
              </div>

              <div className="font-mono text-lg font-bold text-slate-100 mb-2">
                {conflict.candidateA.value} {conflict.candidateA.unit || ''}
              </div>

              <div className="space-y-1 text-xs text-slate-400">
                <div>
                  <span className="font-semibold text-slate-300">Evidence ID: </span>
                  <span className="font-mono text-cyan-400">{conflict.candidateA.sourceEvidenceId}</span>
                </div>
                <div className="truncate" title={conflict.candidateA.sourceFileName}>
                  <span className="font-semibold text-slate-300">Source: </span>
                  {conflict.candidateA.sourceFileName}
                </div>
                <div>
                  <span className="font-semibold text-slate-300">Location: </span>
                  {conflict.candidateA.sourceLocation}
                </div>
                <div>
                  <span className="font-semibold text-slate-300">SHA-256: </span>
                  <span className="font-mono text-[10px] text-slate-500">{truncateHash(conflict.candidateA.evidenceSha256)}</span>
                </div>
              </div>
            </div>

            {/* Candidate B */}
            <div
              onClick={() => setSelectedChoice('candidateB')}
              className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                selectedChoice === 'candidateB'
                  ? 'border-purple-400 bg-purple-950/40 shadow-inner'
                  : 'border-slate-800 bg-slate-900/60 hover:bg-slate-900/90'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-purple-300">
                  Candidate B
                </span>
                <input
                  type="radio"
                  name="candidateChoice"
                  checked={selectedChoice === 'candidateB'}
                  onChange={() => setSelectedChoice('candidateB')}
                  className="text-purple-500 focus:ring-purple-500"
                />
              </div>

              <div className="font-mono text-lg font-bold text-slate-100 mb-2">
                {conflict.candidateB.value} {conflict.candidateB.unit || ''}
              </div>

              <div className="space-y-1 text-xs text-slate-400">
                <div>
                  <span className="font-semibold text-slate-300">Evidence ID: </span>
                  <span className="font-mono text-purple-400">{conflict.candidateB.sourceEvidenceId}</span>
                </div>
                <div className="truncate" title={conflict.candidateB.sourceFileName}>
                  <span className="font-semibold text-slate-300">Source: </span>
                  {conflict.candidateB.sourceFileName}
                </div>
                <div>
                  <span className="font-semibold text-slate-300">Location: </span>
                  {conflict.candidateB.sourceLocation}
                </div>
                <div>
                  <span className="font-semibold text-slate-300">SHA-256: </span>
                  <span className="font-mono text-[10px] text-slate-500">{truncateHash(conflict.candidateB.evidenceSha256)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Option for Reconciled / Custom Value */}
          <div
            onClick={() => setSelectedChoice('custom')}
            className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
              selectedChoice === 'custom'
                ? 'border-cyan-400 bg-cyan-950/30'
                : 'border-slate-800 bg-slate-900/40 hover:bg-slate-900/70'
            }`}
          >
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 mb-1.5 cursor-pointer">
              <input
                type="radio"
                name="candidateChoice"
                checked={selectedChoice === 'custom'}
                onChange={() => setSelectedChoice('custom')}
                className="text-cyan-500 focus:ring-cyan-500"
              />
              <span>Enter Reconciled Technical Value</span>
            </label>
            {selectedChoice === 'custom' && (
              <input
                type="text"
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder="e.g. 230 V (Nominal rating reconciled between operating limits)"
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono mt-2"
              />
            )}
          </div>

          {/* Mandatory Resolution Rationale */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Mandatory Engineering Resolution Rationale <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={3}
              required
              value={rationale}
              onChange={(e) => {
                setRationale(e.target.value);
                setError(null);
              }}
              placeholder="Provide technical justification (e.g., Laboratory test report takes precedence over preliminary marketing datasheet per BIS Clause 4.1 hierarchy)..."
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none"
            />
            {error && <span className="text-[11px] text-rose-400 mt-1 block font-medium">{error}</span>}
          </div>

          {/* Footer Note */}
          <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-[11px] text-slate-400 flex items-center gap-2 font-mono">
            <span className="material-symbols-outlined text-sm text-cyan-400">lock</span>
            Both Candidate A &amp; B source hashes and locations are permanently archived in the immutable audit log.
          </div>

          {/* Submit Action Bar */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-md shadow-amber-500/20 flex items-center gap-1.5 cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm font-bold">how_to_reg</span>
              Commit Conflict Resolution
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
