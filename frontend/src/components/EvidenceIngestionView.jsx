import React, { useState } from 'react';
import { EvidenceCategory, AcceptanceStatus } from '../types/evidenceTypes';
import { truncateHash } from '../utils/evidenceCrypto';

export function EvidenceIngestionView({
  evidenceList = [],
  onOpenAddModal,
  onInspectEvidence,
}) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Filtered evidence items
  const filteredList = evidenceList.filter((item) => {
    const matchesCat =
      selectedCategory === 'ALL' || item.fileType === selectedCategory;
    const matchesStatus =
      selectedStatus === 'ALL' || item.acceptanceStatus === selectedStatus;
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      item.fileName.toLowerCase().includes(q) ||
      item.id.toLowerCase().includes(q) ||
      item.sha256.toLowerCase().includes(q);
    return matchesCat && matchesStatus && matchesSearch;
  });

  const totalCount = evidenceList.length;
  const reviewCount = evidenceList.filter(
    (e) => e.acceptanceStatus === AcceptanceStatus.REQUIRES_REVIEW
  ).length;
  const acceptedCount = evidenceList.filter(
    (e) => e.acceptanceStatus === AcceptanceStatus.ACCEPTED
  ).length;
  const rejectedCount = evidenceList.filter(
    (e) => e.acceptanceStatus === AcceptanceStatus.REJECTED
  ).length;

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-7xl mx-auto">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-[11px] font-mono font-medium mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            STATUTORY EVIDENCE INGESTION
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
            Universal Evidence Ingestion &amp; Repository
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Multi-modal statutory artifact provenance: PDF documents, acoustic inspection recordings, high-resolution imagery, and CAD geometry.
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenAddModal}
          className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 self-start sm:self-auto shadow-md shadow-cyan-500/20 cursor-pointer"
        >
          <span className="material-symbols-outlined text-sm font-bold">add_circle</span>
          Add Evidence
        </button>
      </div>

      {/* Regulatory Integrity Firewall Notice */}
      <div className="p-4 bg-[#0f1422]/90 text-slate-100 rounded-xl flex items-start gap-3 shadow-xl border border-slate-800">
        <span className="material-symbols-outlined text-cyan-400 text-xl mt-0.5">shield</span>
        <div className="flex-1 text-xs">
          <span className="font-mono font-bold text-cyan-300 block mb-0.5 uppercase tracking-wider text-[11px]">
            Cardinal Regulatory Rule: Decoupled State Architecture
          </span>
          <p className="text-slate-300 leading-relaxed text-[11px]">
            <span className="font-mono text-cyan-400 font-semibold">File Processing</span> ≠{' '}
            <span className="font-mono text-cyan-400 font-semibold">Evidence Acceptance</span> ≠{' '}
            <span className="font-mono text-cyan-400 font-semibold">Engineering Assessment</span> ≠{' '}
            <span className="font-mono text-cyan-400 font-semibold">Human Attestation</span> ≠{' '}
            <span className="font-mono text-cyan-400 font-semibold">BIS Certification</span>.
            Extracted files remain strictly in <span className="text-amber-300 font-semibold underline">Requires Review</span> status until affirmatively validated by a designated engineer.
          </p>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Total Ingested Artifacts</span>
          <span className="font-mono text-xl font-bold text-slate-100 mt-1 block">
            {totalCount}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Awaiting Engineer Review</span>
          <span className="font-mono text-xl font-bold text-amber-400 mt-1 block">
            {reviewCount}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Accepted Evidence</span>
          <span className="font-mono text-xl font-bold text-emerald-400 mt-1 block">
            {acceptedCount}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Flagged / Rejected</span>
          <span className="font-mono text-xl font-bold text-rose-400 mt-1 block">
            {rejectedCount}
          </span>
        </div>
      </div>

      {/* Filters & Search Control Bar */}
      <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-3 flex flex-col md:flex-row items-center justify-between gap-3 shadow-xl">
        {/* Category Pill Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar w-full md:w-auto">
          {[
            { id: 'ALL', label: 'All Artifacts' },
            { id: EvidenceCategory.PDF, label: 'PDF Documents' },
            { id: EvidenceCategory.AUDIO, label: 'Audio Records' },
            { id: EvidenceCategory.IMAGE, label: 'Visual Imagery' },
            { id: EvidenceCategory.ENGINEERING, label: 'CAD & Engineering' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setSelectedCategory(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                selectedCategory === tab.id
                  ? 'bg-cyan-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Status Select */}
        <div className="flex items-center gap-2.5 w-full md:w-auto justify-end">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value={AcceptanceStatus.REQUIRES_REVIEW}>Requires Review</option>
            <option value={AcceptanceStatus.ACCEPTED}>Accepted</option>
            <option value={AcceptanceStatus.REJECTED}>Rejected</option>
          </select>

          <div className="relative w-full sm:w-60">
            <span className="material-symbols-outlined text-sm text-slate-500 absolute left-3 top-2">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search filename, ID, hash..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>

      {/* Evidence Repository Table or Empty State */}
      <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {filteredList.length === 0 ? (
          <div className="py-16 px-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 mx-auto mb-3 shadow-inner">
              <span className="material-symbols-outlined text-3xl">policy</span>
            </div>
            <h3 className="text-base font-semibold text-slate-100 mb-1 font-['Space_Grotesk']">
              No evidence uploaded yet
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mb-5 leading-relaxed">
              Ingest BIS standards, laboratory test reports, acoustic inspection recordings, nameplate photos, or CAD engineering geometry to populate the evidence repository.
            </p>
            <button
              type="button"
              onClick={onOpenAddModal}
              className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all inline-flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm font-bold">add_circle</span>
              Add First Evidence Artifact
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/60 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4 font-semibold">EVIDENCE ID</th>
                  <th className="py-3 px-4 font-semibold">ARTIFACT NAME &amp; SUBTYPE</th>
                  <th className="py-3 px-4 font-semibold">CATEGORY</th>
                  <th className="py-3 px-4 font-semibold">SIZE</th>
                  <th className="py-3 px-4 font-semibold">SHA-256 HASH</th>
                  <th className="py-3 px-4 font-semibold">PROCESSING</th>
                  <th className="py-3 px-4 font-semibold">ACCEPTANCE</th>
                  <th className="py-3 px-4 font-semibold text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredList.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-cyan-400">
                      {item.id}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-semibold text-slate-200 block truncate max-w-xs font-['Space_Grotesk']">
                        {item.fileName}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
                        {item.subTypeLabel}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 font-mono text-[11px] text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">
                        <span className="material-symbols-outlined text-xs">
                          {item.fileType === EvidenceCategory.PDF
                            ? 'picture_as_pdf'
                            : item.fileType === EvidenceCategory.AUDIO
                            ? 'graphic_eq'
                            : item.fileType === EvidenceCategory.IMAGE
                            ? 'image'
                            : 'view_in_ar'}
                        </span>
                        {item.fileType}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                      {item.fileSize}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        title={item.sha256}
                        className="font-mono text-[10px] text-cyan-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 select-all cursor-pointer hover:border-cyan-500"
                        onClick={() => navigator.clipboard.writeText(item.sha256)}
                      >
                        {truncateHash(item.sha256, 6, 6)}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                        EXTRACTION COMPLETE
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                          item.acceptanceStatus === AcceptanceStatus.ACCEPTED
                            ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                            : item.acceptanceStatus === AcceptanceStatus.REJECTED
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                            : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                        }`}
                      >
                        {item.acceptanceStatus}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => onInspectEvidence(item)}
                        className="px-2.5 py-1 text-xs font-medium text-cyan-300 hover:text-cyan-200 bg-cyan-950/60 hover:bg-cyan-900/60 rounded-md transition-colors inline-flex items-center gap-1 border border-cyan-800/60 cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-sm">visibility</span>
                        Inspect / Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
