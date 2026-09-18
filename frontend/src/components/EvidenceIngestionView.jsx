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
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[11px] font-mono font-medium mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            STATUTORY EVIDENCE INGESTION
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
            Universal Evidence Ingestion &amp; Repository
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Multi-modal statutory artifact provenance: PDF documents, acoustic inspection recordings, high-resolution imagery, and CAD geometry.
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenAddModal}
          className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 self-start sm:self-auto shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">add_circle</span>
          Add Evidence
        </button>
      </div>

      {/* Regulatory Integrity Firewall Notice */}
      <div className="p-4 bg-slate-900 text-white rounded-lg flex items-start gap-3 shadow-sm border border-slate-800">
        <span className="material-symbols-outlined text-amber-400 text-xl mt-0.5">shield</span>
        <div className="flex-1 text-xs">
          <span className="font-mono font-bold text-amber-300 block mb-0.5 uppercase tracking-wider text-[11px]">
            Cardinal Regulatory Rule: Decoupled State Architecture
          </span>
          <p className="text-slate-300 leading-relaxed text-[11px]">
            <span className="font-mono text-white font-semibold">File Processing</span> ≠{' '}
            <span className="font-mono text-white font-semibold">Evidence Acceptance</span> ≠{' '}
            <span className="font-mono text-white font-semibold">Engineering Assessment</span> ≠{' '}
            <span className="font-mono text-white font-semibold">Human Attestation</span> ≠{' '}
            <span className="font-mono text-white font-semibold">BIS Certification</span>.
            Extracted files remain strictly in <span className="text-amber-300 font-semibold underline">Requires Review</span> status until affirmatively validated by a designated engineer.
          </p>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Total Ingested Artifacts</span>
          <span className="font-mono text-xl font-bold text-[#0F172A] mt-1 block">
            {totalCount}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Awaiting Engineer Review</span>
          <span className="font-mono text-xl font-bold text-amber-600 mt-1 block">
            {reviewCount}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Accepted Evidence</span>
          <span className="font-mono text-xl font-bold text-emerald-600 mt-1 block">
            {acceptedCount}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Flagged / Rejected</span>
          <span className="font-mono text-xl font-bold text-red-600 mt-1 block">
            {rejectedCount}
          </span>
        </div>
      </div>

      {/* Filters & Search Control Bar */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg p-3 flex flex-col md:flex-row items-center justify-between gap-3 shadow-sm">
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
              className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === tab.id
                  ? 'bg-blue-50 text-[#1D4ED8] font-semibold border border-blue-200'
                  : 'text-[#64748B] hover:text-[#0F172A]'
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
            className="px-2.5 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] focus:outline-none focus:border-[#1D4ED8]"
          >
            <option value="ALL">All Statuses</option>
            <option value={AcceptanceStatus.REQUIRES_REVIEW}>Requires Review</option>
            <option value={AcceptanceStatus.ACCEPTED}>Accepted</option>
            <option value={AcceptanceStatus.REJECTED}>Rejected</option>
          </select>

          <div className="relative w-full sm:w-60">
            <span className="material-symbols-outlined text-sm text-[#94A3B8] absolute left-2.5 top-2">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search filename, ID, hash..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white"
            />
          </div>
        </div>
      </div>

      {/* Evidence Repository Table or Empty State */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
        {filteredList.length === 0 ? (
          <div className="py-16 px-4 text-center">
            <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-3">
              <span className="material-symbols-outlined text-3xl">policy</span>
            </div>
            <h3 className="text-base font-semibold text-[#0F172A] mb-1">
              No evidence uploaded yet
            </h3>
            <p className="text-xs text-[#64748B] max-w-md mx-auto mb-5 leading-relaxed">
              Ingest BIS standards, laboratory test reports, acoustic inspection recordings, nameplate photos, or CAD engineering geometry to populate the evidence repository.
            </p>
            <button
              type="button"
              onClick={onOpenAddModal}
              className="px-4 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors inline-flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add_circle</span>
              Add First Evidence Artifact
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#F8F9FA] border-b border-[#E2E8F0] font-mono text-[11px] text-[#64748B]">
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
              <tbody>
                {filteredList.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-[#E2E8F0] hover:bg-[#F8F9FA] transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-[#1D4ED8]">
                      {item.id}
                    </td>

                    <td className="py-3 px-4">
                      <span className="font-semibold text-[#0F172A] block truncate max-w-xs">
                        {item.fileName}
                      </span>
                      <span className="text-[10px] text-[#64748B] font-mono block mt-0.5">
                        {item.subTypeLabel}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-[#E2E8F0]">
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

                    <td className="py-3 px-4 font-mono text-[11px] text-[#64748B]">
                      {item.fileSize}
                    </td>

                    <td className="py-3 px-4">
                      <span
                        title={item.sha256}
                        className="font-mono text-[10px] text-slate-600 bg-[#F1F5F9] px-2 py-0.5 rounded border border-[#E2E8F0] select-all cursor-pointer"
                        onClick={() => navigator.clipboard.writeText(item.sha256)}
                      >
                        {truncateHash(item.sha256, 6, 6)}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        EXTRACTION COMPLETE
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                          item.acceptanceStatus === AcceptanceStatus.ACCEPTED
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : item.acceptanceStatus === AcceptanceStatus.REJECTED
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {item.acceptanceStatus}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => onInspectEvidence(item)}
                        className="px-2.5 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-blue-50 rounded transition-colors inline-flex items-center gap-1 border border-transparent hover:border-blue-200"
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
