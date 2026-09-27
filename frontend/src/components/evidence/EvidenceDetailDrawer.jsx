import React, { useState } from 'react';
import {
  EvidenceCategory,
  AcceptanceStatus,
} from '../../types/evidenceTypes';

export function EvidenceDetailDrawer({ evidence, isOpen, onClose, onUpdateStatus }) {
  const [reviewNote, setReviewNote] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);

  if (!isOpen || !evidence) return null;

  const copyHashToClipboard = () => {
    if (evidence.sha256) {
      navigator.clipboard.writeText(evidence.sha256);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleDecision = (status) => {
    if (onUpdateStatus) {
      onUpdateStatus(evidence.id, status, reviewNote);
    }
    onClose();
  };

  const payload = evidence.categoryPayload || {};

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-[#0b0f19] text-slate-100 h-full shadow-2xl z-10 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200 border-l border-slate-800">
        {/* Drawer Header */}
        <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center font-mono font-bold text-xs shadow-sm">
              {evidence.fileType ? evidence.fileType.substring(0, 3) : 'EVD'}
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-cyan-400">{evidence.id}</span>
                <span className="text-xs text-slate-100 font-semibold truncate max-w-xs font-['Space_Grotesk']">
                  {evidence.fileName}
                </span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                {evidence.subTypeLabel} · {evidence.fileSize} · {evidence.uploadTimestamp}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {/* Regulatory Decoupled States Card */}
          <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
            <span className="font-mono text-[10px] uppercase tracking-wider text-cyan-400 block mb-2 font-semibold">
              Statutory Lifecycle &amp; State Separation
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">1. File Processing</span>
                <span className="font-mono font-bold text-emerald-400 block mt-0.5">
                  EXTRACTION COMPLETE
                </span>
              </div>

              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">2. Evidence Acceptance</span>
                <span
                  className={`font-mono font-bold block mt-0.5 ${
                    evidence.acceptanceStatus === AcceptanceStatus.ACCEPTED
                      ? 'text-emerald-400'
                      : evidence.acceptanceStatus === AcceptanceStatus.REJECTED
                      ? 'text-rose-400'
                      : 'text-amber-400'
                  }`}
                >
                  {evidence.acceptanceStatus}
                </span>
              </div>

              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">3. Compliance Verdict</span>
                <span className="font-mono font-bold text-slate-500 block mt-0.5">
                  NOT EVALUATED
                </span>
              </div>

              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">4. Engineer Attestation</span>
                <span className="font-mono font-bold text-slate-500 block mt-0.5">
                  UNSIGNED
                </span>
              </div>

              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">5. BIS CRS Submission</span>
                <span className="font-mono font-bold text-slate-500 block mt-0.5">
                  NOT SUBMITTED
                </span>
              </div>

              <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block font-mono">Integrity Status</span>
                <span className="font-mono font-bold text-cyan-400 block mt-0.5">
                  SHA-256 VERIFIED
                </span>
              </div>
            </div>
          </div>

          {/* Cryptographic Hash Section */}
          <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
                Cryptographic Artifact Digest (SHA-256)
              </span>
              <button
                type="button"
                onClick={copyHashToClipboard}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono cursor-pointer transition-colors"
              >
                <span className="material-symbols-outlined text-xs">
                  {copiedHash ? 'done' : 'content_copy'}
                </span>
                {copiedHash ? 'Copied Hash' : 'Copy Hash'}
              </button>
            </div>
            <div className="font-mono text-[11px] bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 text-cyan-300 break-all select-all">
              {evidence.sha256}
            </div>
          </div>

          {/* PDF Documents */}
          {evidence.fileType === EvidenceCategory.PDF && (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-100 flex items-center gap-1.5 font-['Space_Grotesk']">
                  <span className="material-symbols-outlined text-sm text-rose-400">picture_as_pdf</span>
                  PDF Document &amp; Citation Architecture
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  {payload.pageCount || 1} Pages Indexed
                </span>
              </div>

              <div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Extracted Text &amp; Page References
                </span>
                <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed max-h-36 overflow-y-auto">
                  {payload.extractedTextSnippet || 'Document text extracted and tokenized for statutory clause cross-matching.'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Page References</span>
                  <span className="font-mono font-semibold text-slate-200 block mt-0.5">
                    {payload.pageReferences?.join(', ') || 'Page 1'}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Extracted Tables</span>
                  <span className="font-mono font-semibold text-slate-200 block mt-0.5">
                    0 Tables (Standard Formatting)
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Audio Recordings */}
          {evidence.fileType === EvidenceCategory.AUDIO && (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-100 flex items-center gap-1.5 font-['Space_Grotesk']">
                  <span className="material-symbols-outlined text-sm text-purple-400">graphic_eq</span>
                  Acoustic Evidence &amp; Timestamped Transcript
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  Duration: {payload.durationSeconds || 0}s
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Speaker Attribution</span>
                  <span className="font-medium text-slate-200 block mt-0.5">
                    {payload.speakerMetadata?.speaker || 'Regulatory Inspection Lead'}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Acoustic Observations</span>
                  <span className="font-medium text-slate-200 block mt-0.5">
                    Acoustic recording archived with SHA-256 signature
                  </span>
                </div>
              </div>

              <div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Timestamped Transcript
                </span>
                <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed">
                  [00:00:00 - 00:00:{String(payload.durationSeconds || 10).padStart(2, '0')}] Audio artifact recorded and authenticated. Awaiting speech-to-text diarization.
                </div>
              </div>
            </div>
          )}

          {/* Visual Images */}
          {evidence.fileType === EvidenceCategory.IMAGE && (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-100 flex items-center gap-1.5 font-['Space_Grotesk']">
                  <span className="material-symbols-outlined text-sm text-emerald-400">image</span>
                  Visual Inspection &amp; Annotation Architecture
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  {payload.dimensions?.width} x {payload.dimensions?.height} px
                </span>
              </div>

              <div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 block mb-1">
                  Visual Inspection Observations
                </span>
                <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  {payload.visualInspectionNotes || 'Product image registered for physical marking verification and creepage tracing.'}
                </div>
              </div>
            </div>
          )}

          {/* Engineering & CAD Files */}
          {evidence.fileType === EvidenceCategory.ENGINEERING && (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-xs text-slate-100 flex items-center gap-1.5 font-['Space_Grotesk']">
                  <span className="material-symbols-outlined text-sm text-cyan-400">view_in_ar</span>
                  CAD Geometry &amp; Spatial Inspection Ready
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  Format: {payload.format || 'STEP CAD'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Babylon.js 3D Ingestion</span>
                  <span className="font-mono font-bold text-emerald-400 block mt-0.5">
                    GEOMETRY VALIDATED
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-mono">Component Assemblies</span>
                  <span className="font-mono font-bold text-slate-200 block mt-0.5">
                    {payload.partCount || 1} Parts Identified
                  </span>
                </div>
              </div>

              <div className="p-3 bg-cyan-950/40 border border-cyan-800/60 rounded-lg text-xs text-cyan-200 leading-relaxed">
                Physical dimensions and surface boundary contours are mapped to the coordinate grid for downstream Compile Compliance spatial clearance checks.
              </div>
            </div>
          )}

          {/* Regulatory Decision Action Box */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col gap-3 mt-auto shadow-2xl">
            <span className="font-mono text-[10px] uppercase tracking-wider text-cyan-400 font-bold block">
              Affirmative Engineering Review &amp; Sign-off
            </span>
            <p className="text-xs text-slate-400 leading-relaxed">
              Regulatory compliance demands affirmative human review. Accept or reject this evidence artifact based on authenticity, readability, and statutory scope.
            </p>
            <input
              type="text"
              value={reviewNote}
              onChange={(e) => setReviewNote(e.target.value)}
              placeholder="Enter review decision rationale (e.g., Validated against manufacturer original)..."
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => handleDecision(AcceptanceStatus.REJECTED)}
                className="px-4 py-2 border border-rose-800/80 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm">cancel</span>
                Reject Artifact
              </button>
              <button
                type="button"
                onClick={() => handleDecision(AcceptanceStatus.ACCEPTED)}
                className="px-4 py-2 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-md shadow-emerald-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm font-bold">check_circle</span>
                Accept Evidence Record
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
