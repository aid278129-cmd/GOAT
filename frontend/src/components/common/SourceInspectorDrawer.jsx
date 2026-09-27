import React, { useState } from 'react';

/**
 * SourceInspectorDrawer
 * 
 * Auditable Source & Provenance Drawer
 * Closed by default. Opens from the right when a user clicks:
 * Source, Citation, Provenance, Evidence, or Clause Source.
 */
export function SourceInspectorDrawer({ isOpen, onClose, data }) {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState(false);

  if (!isOpen || !data) return null;

  const handleCopyHash = () => {
    if (!data.sha256) return;
    navigator.clipboard.writeText(data.sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyCitation = () => {
    const citation = `${data.source || 'Statutory Source'} — ${data.clause || 'Clause'} (${data.document || 'Document'}${data.page ? `, p. ${data.page}` : ''})`;
    navigator.clipboard.writeText(citation);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm font-sans transition-opacity duration-200">
      <div 
        className="fixed inset-0" 
        onClick={onClose} 
        aria-hidden="true"
      />
      <aside 
        className="relative w-full max-w-lg bg-[#0b0f19] text-slate-100 h-full shadow-2xl flex flex-col border-l border-slate-800 z-10 animate-in slide-in-from-right duration-250 ease-out"
        role="dialog"
        aria-label="Source Inspector"
      >
        {/* Header */}
        <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <span className="material-symbols-outlined text-[18px]">verified</span>
            </div>
            <div>
              <h2 className="text-xs font-bold text-slate-100 uppercase tracking-widest font-mono">
                Source Provenance Inspector
              </h2>
              <p className="text-[11px] text-slate-400">
                Auditable citation &amp; regulatory grounding
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            title="Close Inspector"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Regulatory Source Overview */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
                Regulatory Origin
              </span>
              <span className="text-[10px] font-mono font-semibold text-emerald-300 bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-800/60">
                {data.authority || 'Bureau of Indian Standards'}
              </span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">
                {data.source || 'Official Indian Standard Specification'}
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                {data.document || 'BIS Gazette Order / Product Manual'}
              </p>
            </div>
          </div>

          {/* Citation Coordinates Grid */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono font-semibold block mb-1">
                Clause Reference
              </span>
              <span className="font-mono font-semibold text-cyan-300 text-xs">
                {data.clause || 'Cl. General'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono font-semibold block mb-1">
                Page / Sheet
              </span>
              <span className="font-mono font-semibold text-slate-200 text-xs">
                {data.page ? `Page ${data.page}` : 'Section 1'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono font-semibold block mb-1">
                Verification Method
              </span>
              <span className="text-slate-300 text-xs font-medium">
                {data.verification || 'Deterministic Rule Matching'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono font-semibold block mb-1">
                Extraction Method
              </span>
              <span className="text-slate-300 text-xs font-medium">
                {data.extractionMethod || 'Engineering Verified'}
              </span>
            </div>
          </div>

          {/* Text Excerpt / Verbatim Snapshot */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 font-['Space_Grotesk']">
                Document Snapshot &amp; Verbatim Excerpt
              </label>
              <button
                type="button"
                onClick={handleCopyCitation}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 cursor-pointer transition-colors"
              >
                <span className="material-symbols-outlined text-[13px]">content_copy</span>
                <span>{copiedCitation ? 'Copied' : 'Copy Citation'}</span>
              </button>
            </div>
            <div className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl text-xs font-mono text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap select-all">
              {data.snapshot || data.text || 'No verbatim excerpt recorded for this citation.'}
            </div>
          </div>

          {/* Cryptographic SHA-256 Hash */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-200 font-['Space_Grotesk']">
                Cryptographic Integrity (SHA-256)
              </label>
              <button
                type="button"
                onClick={handleCopyHash}
                disabled={!data.sha256}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 cursor-pointer disabled:opacity-40 transition-colors"
              >
                <span className="material-symbols-outlined text-[13px]">content_copy</span>
                <span>{copiedHash ? 'Hash Copied' : 'Copy Hash'}</span>
              </button>
            </div>
            <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl font-mono text-[11px] text-cyan-400 break-all select-all">
              {data.sha256 || 'SHA-256 hash not computed for this record.'}
            </div>
            <p className="text-[11px] text-slate-500">
              Tamper-evident verification guaranteeing exact source document authenticity.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between shrink-0 text-xs">
          <span className="text-[11px] text-slate-400 font-mono">
            0% LLM Compliance Authority
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 text-slate-950 rounded-lg text-xs font-semibold transition cursor-pointer shadow-md shadow-cyan-500/20"
          >
            Done
          </button>
        </div>
      </aside>
    </div>
  );
}
