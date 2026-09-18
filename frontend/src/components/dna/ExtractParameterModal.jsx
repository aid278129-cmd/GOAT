import React, { useState } from 'react';
import { CANONICAL_PARAMETERS, DNASection } from '../../types/productDnaTypes';
import { AcceptanceStatus } from '../../types/evidenceTypes';

export function ExtractParameterModal({
  isOpen,
  onClose,
  evidenceList = [],
  onExtractParameter,
  preselectedEvidence = null,
}) {
  const acceptedEvidence = evidenceList.filter(
    (e) => e.acceptanceStatus === AcceptanceStatus.ACCEPTED
  );

  const [selectedEvidenceId, setSelectedEvidenceId] = useState(
    preselectedEvidence?.id || (acceptedEvidence[0]?.id || '')
  );
  const [selectedParamId, setSelectedParamId] = useState(CANONICAL_PARAMETERS[0].id);
  const [extractedValue, setExtractedValue] = useState('');
  const [customUnit, setCustomUnit] = useState('');
  const [location, setLocation] = useState('Page 1');
  const [extractionMethod, setExtractionMethod] = useState('DIRECT_DOCUMENT_EXTRACTION');
  const [confidence, setConfidence] = useState('0.95');

  if (!isOpen) return null;

  const currentEvidence = acceptedEvidence.find((e) => e.id === selectedEvidenceId);
  const currentParam = CANONICAL_PARAMETERS.find((p) => p.id === selectedParamId);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!currentEvidence || !extractedValue.trim()) return;

    onExtractParameter({
      evidence: currentEvidence,
      parameterId: currentParam.id,
      parameterName: currentParam.name,
      section: currentParam.section,
      extractedValue: extractedValue.trim(),
      unit: customUnit.trim() || currentParam.defaultUnit || '',
      location: location.trim() || 'Document Body',
      extractionMethod,
      confidence: parseFloat(confidence) || 1.0,
    });

    onClose();
    setExtractedValue('');
    setCustomUnit('');
    setLocation('Page 1');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white border border-[#E2E8F0] rounded-xl max-w-lg w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8F9FA]">
          <div className="flex items-center gap-2.5">
            <span className="w-8 h-8 rounded bg-[#1D4ED8] text-white flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-base">fingerprint</span>
            </span>
            <div>
              <h3 className="font-bold text-sm text-[#0F172A]">
                Extract Verified Parameter into Product DNA
              </h3>
              <span className="text-[10px] font-mono text-[#64748B] block">
                ACCEPTED EVIDENCE GATED // PROVENANCE BINDING
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

        {/* Content */}
        {acceptedEvidence.length === 0 ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
              <span className="material-symbols-outlined text-2xl">gavel</span>
            </div>
            <h4 className="text-sm font-bold text-[#0F172A]">
              No Accepted Evidence Available
            </h4>
            <p className="text-xs text-[#64748B] max-w-sm mx-auto leading-relaxed">
              Under strict evidence gating rules, parameters can only be derived from artifacts that have been reviewed and affirmatively <span className="font-semibold text-emerald-700">ACCEPTED</span> by an engineer.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="mt-2 px-4 py-2 bg-slate-900 text-white rounded text-xs font-semibold hover:bg-black"
            >
              Go to Evidence Ingestion &amp; Review
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4 overflow-y-auto">
            {/* Accepted Evidence Selector */}
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Source Accepted Evidence Artifact <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedEvidenceId}
                onChange={(e) => setSelectedEvidenceId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
              >
                {acceptedEvidence.map((ev) => (
                  <option key={ev.id} value={ev.id}>
                    [{ev.id}] {ev.fileName} ({ev.subTypeLabel})
                  </option>
                ))}
              </select>
              {currentEvidence && (
                <div className="mt-1.5 flex items-center gap-2 text-[10px] font-mono text-[#64748B]">
                  <span className="text-emerald-700 font-semibold flex items-center gap-1">
                    <span className="material-symbols-outlined text-xs">verified</span>
                    ACCEPTED
                  </span>
                  <span>·</span>
                  <span>SHA-256: {currentEvidence.sha256.substring(0, 12)}...</span>
                </div>
              )}
            </div>

            {/* Target Parameter Selector */}
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Target Product DNA Parameter <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedParamId}
                onChange={(e) => {
                  setSelectedParamId(e.target.value);
                  const p = CANONICAL_PARAMETERS.find((param) => param.id === e.target.value);
                  if (p?.defaultUnit) setCustomUnit(p.defaultUnit);
                }}
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
              >
                {Object.values(DNASection).map((sec) => (
                  <optgroup key={sec.id} label={sec.title}>
                    {CANONICAL_PARAMETERS.filter((p) => p.section === sec.id).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.defaultUnit ? `(${p.defaultUnit})` : ''}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            {/* Extracted Value & Unit */}
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Extracted Parameter Value <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={extractedValue}
                  onChange={(e) => setExtractedValue(e.target.value)}
                  placeholder="e.g. 230 or 5000 or IP65"
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] font-mono focus:outline-none focus:border-[#1D4ED8]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Physical Unit
                </label>
                <input
                  type="text"
                  value={customUnit || currentParam?.defaultUnit || ''}
                  onChange={(e) => setCustomUnit(e.target.value)}
                  placeholder="e.g. V, W, mm"
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] font-mono focus:outline-none focus:border-[#1D4ED8]"
                />
              </div>
            </div>

            {/* Source Location Reference */}
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                Source Location / Citation in Artifact <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Page 4, Section 3.2, Table 1 or 00:02:15 audio observation"
                className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
              />
            </div>

            {/* Extraction Method */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Extraction Method
                </label>
                <select
                  value={extractionMethod}
                  onChange={(e) => setExtractionMethod(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
                >
                  <option value="DIRECT_DOCUMENT_EXTRACTION">Document Text Extraction</option>
                  <option value="OPENDATALOADER_PDF">PDF Structural Parser</option>
                  <option value="IMAGE_OCR">Optical Character Recognition (OCR)</option>
                  <option value="VOICE_TRANSCRIPT">Acoustic Audio Diarization</option>
                  <option value="BOM_PARSER">BOM Component Parser</option>
                  <option value="CAD_GEOMETRY">CAD 3D Geometry Measurement</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Confidence Score
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={confidence}
                  onChange={(e) => setConfidence(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] font-mono focus:outline-none focus:border-[#1D4ED8]"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between">
              <span className="text-[10px] font-mono text-[#64748B]">
                Conflict detection runs automatically on commit.
              </span>
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#1D4ED8] hover:bg-[#1E40AF] text-white rounded text-xs font-semibold transition-colors shadow-sm flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-sm">save</span>
                  Commit Parameter to DNA
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
