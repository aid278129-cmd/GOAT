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
      <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white border border-[#E2E8F0] rounded-xl max-w-2xl w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between bg-amber-50">
          <div className="flex items-center gap-2.5">
            <span className="w-8 h-8 rounded bg-amber-600 text-white flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-base">warning</span>
            </span>
            <div>
              <h3 className="font-bold text-sm text-[#0F172A]">
                Parameter Conflict Resolution
              </h3>
              <span className="text-[10px] font-mono text-amber-800 font-medium block">
                MANDATORY HUMAN ENGINEERING REVIEW // AUDITABLE RESOLUTION
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#64748B] hover:text-[#0F172A] p-1 rounded"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleResolveSubmit} className="p-6 flex flex-col gap-5 overflow-y-auto">
          <div>
            <span className="text-xs text-[#64748B] block font-mono">Discrepancy Detected for:</span>
            <h4 className="text-base font-bold text-[#0F172A]">{conflict.parameterName}</h4>
            <p className="text-xs text-[#475569] mt-0.5 leading-relaxed">
              Two accepted evidence artifacts specify differing values. Under regulatory integrity rules, the system will not automatically select a value. Affirmative engineering resolution is required.
            </p>
          </div>

          {/* Side-by-Side Candidates */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Candidate A */}
            <div
              onClick={() => setSelectedChoice('candidateA')}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedChoice === 'candidateA'
                  ? 'border-[#1D4ED8] bg-blue-50/50 shadow-sm'
                  : 'border-[#E2E8F0] bg-[#F8F9FA] hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-blue-800">
                  Candidate A
                </span>
                <input
                  type="radio"
                  name="candidateChoice"
                  checked={selectedChoice === 'candidateA'}
                  onChange={() => setSelectedChoice('candidateA')}
                  className="text-blue-600"
                />
              </div>

              <div className="font-mono text-lg font-bold text-[#0F172A] mb-2">
                {conflict.candidateA.value} {conflict.candidateA.unit || ''}
              </div>

              <div className="space-y-1 text-xs text-[#64748B]">
                <div>
                  <span className="font-semibold text-[#0F172A]">Evidence ID: </span>
                  <span className="font-mono">{conflict.candidateA.sourceEvidenceId}</span>
                </div>
                <div className="truncate" title={conflict.candidateA.sourceFileName}>
                  <span className="font-semibold text-[#0F172A]">Source: </span>
                  {conflict.candidateA.sourceFileName}
                </div>
                <div>
                  <span className="font-semibold text-[#0F172A]">Location: </span>
                  {conflict.candidateA.sourceLocation}
                </div>
                <div>
                  <span className="font-semibold text-[#0F172A]">SHA-256: </span>
                  <span className="font-mono text-[10px]">{truncateHash(conflict.candidateA.evidenceSha256)}</span>
                </div>
              </div>
            </div>

            {/* Candidate B */}
            <div
              onClick={() => setSelectedChoice('candidateB')}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedChoice === 'candidateB'
                  ? 'border-[#1D4ED8] bg-blue-50/50 shadow-sm'
                  : 'border-[#E2E8F0] bg-[#F8F9FA] hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-purple-800">
                  Candidate B
                </span>
                <input
                  type="radio"
                  name="candidateChoice"
                  checked={selectedChoice === 'candidateB'}
                  onChange={() => setSelectedChoice('candidateB')}
                  className="text-blue-600"
                />
              </div>

              <div className="font-mono text-lg font-bold text-[#0F172A] mb-2">
                {conflict.candidateB.value} {conflict.candidateB.unit || ''}
              </div>

              <div className="space-y-1 text-xs text-[#64748B]">
                <div>
                  <span className="font-semibold text-[#0F172A]">Evidence ID: </span>
                  <span className="font-mono">{conflict.candidateB.sourceEvidenceId}</span>
                </div>
                <div className="truncate" title={conflict.candidateB.sourceFileName}>
                  <span className="font-semibold text-[#0F172A]">Source: </span>
                  {conflict.candidateB.sourceFileName}
                </div>
                <div>
                  <span className="font-semibold text-[#0F172A]">Location: </span>
                  {conflict.candidateB.sourceLocation}
                </div>
                <div>
                  <span className="font-semibold text-[#0F172A]">SHA-256: </span>
                  <span className="font-mono text-[10px]">{truncateHash(conflict.candidateB.evidenceSha256)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Option for Reconciled / Custom Value */}
          <div
            onClick={() => setSelectedChoice('custom')}
            className={`p-3 rounded-lg border transition-colors cursor-pointer ${
              selectedChoice === 'custom'
                ? 'border-[#1D4ED8] bg-blue-50/30'
                : 'border-[#E2E8F0] bg-white'
            }`}
          >
            <label className="flex items-center gap-2 text-xs font-semibold text-[#0F172A] mb-1.5 cursor-pointer">
              <input
                type="radio"
                name="candidateChoice"
                checked={selectedChoice === 'custom'}
                onChange={() => setSelectedChoice('custom')}
                className="text-blue-600"
              />
              <span>Enter Reconciled Technical Value</span>
            </label>
            {selectedChoice === 'custom' && (
              <input
                type="text"
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder="e.g. 230 V (Nominal rating reconciled between operating limits)"
                className="w-full px-3 py-1.5 text-xs bg-white border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
              />
            )}
          </div>

          {/* Mandatory Resolution Rationale */}
          <div>
            <label className="block text-xs font-semibold text-[#0F172A] mb-1">
              Mandatory Engineering Resolution Rationale <span className="text-red-500">*</span>
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
              className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8] focus:bg-white resize-none"
            />
            {error && <span className="text-[11px] text-red-600 mt-1 block font-medium">{error}</span>}
          </div>

          {/* Footer Note */}
          <div className="p-3 bg-slate-100 rounded text-[11px] text-[#64748B] flex items-center gap-2 font-mono">
            <span className="material-symbols-outlined text-sm text-slate-500">lock</span>
            Both Candidate A &amp; B source hashes and locations are permanently archived in the immutable audit log.
          </div>

          {/* Submit Action Bar */}
          <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-semibold transition-colors shadow-sm flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-sm">how_to_reg</span>
              Commit Conflict Resolution
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
