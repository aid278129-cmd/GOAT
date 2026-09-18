import React, { useState } from 'react';
import { DNASection, CANONICAL_PARAMETERS, ParameterReviewStatus } from '../types/productDnaTypes';
import { truncateHash } from '../utils/evidenceCrypto';

export function ProductDNAWorkspaceView({
  productDnaFacts = {},
  conflictsList = [],
  auditLog = [],
  onOpenExtractModal,
  onOpenConflictModal,
}) {
  const [selectedSection, setSelectedSection] = useState('ALL');
  const [auditDrawerOpen, setAuditDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const activeConflicts = conflictsList.filter((c) => c.status === 'PENDING_RESOLUTION');
  const populatedFactsCount = Object.keys(productDnaFacts).length;

  const sectionsList = Object.values(DNASection);

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[11px] font-mono font-medium mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            ACCEPTED EVIDENCE → STRUCTURED PRODUCT DNA
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
            Structured Product DNA &amp; Provenance Workstation
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Deterministic technical parameters derived strictly from Accepted Evidence artifacts.
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setAuditDrawerOpen(true)}
            className="px-3.5 py-2 text-xs font-medium text-[#0F172A] bg-white border border-[#E2E8F0] hover:bg-[#F8F9FA] rounded transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">history</span>
            Audit Trail ({auditLog.length})
          </button>
          <button
            type="button"
            onClick={onOpenExtractModal}
            className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <span className="material-symbols-outlined text-sm">add_link</span>
            Extract Verified Parameter
          </button>
        </div>
      </div>

      {/* Regulatory Boundary Firewall Notice */}
      <div className="p-4 bg-slate-900 text-white rounded-lg flex items-start gap-3 shadow-sm border border-slate-800">
        <span className="material-symbols-outlined text-blue-400 text-xl mt-0.5">hub</span>
        <div className="flex-1 text-xs">
          <span className="font-mono font-bold text-blue-300 block mb-0.5 uppercase tracking-wider text-[11px]">
            Statutory Pipeline Invariant: Provenance Chain
          </span>
          <p className="text-slate-300 leading-relaxed text-[11px]">
            <span className="font-mono text-white font-semibold">Evidence (Accepted)</span> →{' '}
            <span className="font-mono text-white font-semibold">Product DNA</span> →{' '}
            <span className="font-mono text-white font-semibold">Engineering Assessment</span> →{' '}
            <span className="font-mono text-white font-semibold">Human Attestation</span> →{' '}
            <span className="font-mono text-white font-semibold">BIS Submission</span>.
            Product DNA parameters represent empirical characteristics. No parameter is automatically marked as <span className="font-mono text-slate-400">PASS</span>, <span className="font-mono text-slate-400">COMPLIANT</span>, or <span className="font-mono text-slate-400">CERTIFIED</span>.
          </p>
        </div>
      </div>

      {/* Active Conflict Warning Banner */}
      {activeConflicts.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-amber-200 text-amber-900 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-base">warning</span>
            </span>
            <div>
              <h4 className="text-xs font-bold text-amber-950 uppercase tracking-wider font-mono">
                {activeConflicts.length} Parameter Conflict{activeConflicts.length > 1 ? 's' : ''} Require Human Resolution
              </h4>
              <p className="text-xs text-amber-800 mt-0.5">
                Multiple accepted evidence sources specify differing values. Autonomous resolution is barred.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onOpenConflictModal(activeConflicts[0])}
            className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded transition-colors self-start sm:self-auto shadow-sm flex items-center gap-1.5"
          >
            <span className="material-symbols-outlined text-sm">how_to_reg</span>
            Resolve Conflict ({activeConflicts[0].parameterName})
          </button>
        </div>
      )}

      {/* Stats Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Verified Parameters</span>
          <span className="font-mono text-xl font-bold text-[#0F172A] mt-1 block">
            {populatedFactsCount} / {CANONICAL_PARAMETERS.length}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Accepted Backing Artifacts</span>
          <span className="font-mono text-xl font-bold text-emerald-600 mt-1 block">
            {new Set(Object.values(productDnaFacts).map((f) => f.sourceEvidenceId).filter(Boolean)).size}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Active Parameter Conflicts</span>
          <span className="font-mono text-xl font-bold text-amber-600 mt-1 block">
            {activeConflicts.length}
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3.5 shadow-sm">
          <span className="text-[11px] text-[#64748B] block font-medium">Audit Trail Events</span>
          <span className="font-mono text-xl font-bold text-purple-600 mt-1 block">
            {auditLog.length}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg p-3 flex flex-col md:flex-row items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar w-full md:w-auto">
          <button
            type="button"
            onClick={() => setSelectedSection('ALL')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-colors ${
              selectedSection === 'ALL'
                ? 'bg-blue-50 text-[#1D4ED8] font-semibold border border-blue-200'
                : 'text-[#64748B] hover:text-[#0F172A]'
            }`}
          >
            All Sections
          </button>
          {sectionsList.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => setSelectedSection(sec.id)}
              className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                selectedSection === sec.id
                  ? 'bg-blue-50 text-[#1D4ED8] font-semibold border border-blue-200'
                  : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              {sec.title}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <span className="material-symbols-outlined text-sm text-[#94A3B8] absolute left-2.5 top-2">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search parameter, source, or value..."
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8]"
          />
        </div>
      </div>

      {/* 9 Structured Product DNA Sections */}
      <div className="flex flex-col gap-6">
        {sectionsList
          .filter((sec) => selectedSection === 'ALL' || selectedSection === sec.id)
          .map((sec) => {
            const sectionParams = CANONICAL_PARAMETERS.filter((p) => p.section === sec.id);
            const populatedInSection = sectionParams.filter(
              (p) => productDnaFacts[p.id]?.value !== undefined && productDnaFacts[p.id]?.value !== null
            );

            // Filter by search query if present
            const visibleParams = populatedInSection.filter((p) => {
              const f = productDnaFacts[p.id];
              const q = searchQuery.toLowerCase().trim();
              if (!q) return true;
              return (
                p.name.toLowerCase().includes(q) ||
                String(f.value).toLowerCase().includes(q) ||
                f.sourceEvidenceId?.toLowerCase().includes(q) ||
                f.sourceFileName?.toLowerCase().includes(q)
              );
            });

            return (
              <div
                key={sec.id}
                className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm flex flex-col"
              >
                {/* Section Header */}
                <div className="px-5 py-3.5 bg-[#F8F9FA] border-b border-[#E2E8F0] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-[#1D4ED8] text-base">
                      {sec.icon}
                    </span>
                    <div>
                      <h3 className="font-bold text-xs text-[#0F172A] uppercase tracking-wider font-mono">
                        {sec.title}
                      </h3>
                      <span className="text-[11px] text-[#64748B] block mt-0.5">
                        {sec.description}
                      </span>
                    </div>
                  </div>
                  <span className="font-mono text-xs text-[#64748B] bg-white px-2 py-0.5 rounded border border-[#E2E8F0]">
                    {populatedInSection.length} / {sectionParams.length} Parameters
                  </span>
                </div>

                {/* Section Content */}
                <div className="p-5">
                  {populatedInSection.length === 0 ? (
                    /* Initial Clean Empty State */
                    <div className="py-8 px-4 text-center border-2 border-dashed border-[#E2E8F0] rounded-lg bg-[#F8F9FA]/50">
                      <span className="material-symbols-outlined text-2xl text-slate-400 mb-1 block">
                        fact_check
                      </span>
                      <h4 className="text-xs font-semibold text-[#0F172A] mb-0.5">
                        No verified parameters available.
                      </h4>
                      <p className="text-[11px] text-[#64748B] max-w-sm mx-auto mb-3">
                        Parameters in {sec.title} will populate only when evidence artifacts are reviewed and ACCEPTED by an engineer.
                      </p>
                      <button
                        type="button"
                        onClick={onOpenExtractModal}
                        className="px-3 py-1.5 text-xs text-[#1D4ED8] bg-white border border-[#E2E8F0] hover:bg-slate-50 font-medium rounded transition-colors inline-flex items-center gap-1 shadow-2xs"
                      >
                        <span className="material-symbols-outlined text-xs">add_link</span>
                        Extract Parameter
                      </button>
                    </div>
                  ) : (
                    /* Populated Verified Parameters Grid */
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {visibleParams.map((param) => {
                        const fact = productDnaFacts[param.id];
                        const isConflicting = fact.reviewStatus === ParameterReviewStatus.CONFLICTING;
                        const isResolved = fact.reviewStatus === ParameterReviewStatus.ENGINEER_RESOLVED;

                        return (
                          <div
                            key={param.id}
                            className={`p-4 rounded-lg border transition-all flex flex-col justify-between ${
                              isConflicting
                                ? 'border-amber-400 bg-amber-50/40 shadow-xs'
                                : 'border-[#E2E8F0] bg-white hover:border-slate-300'
                            }`}
                          >
                            <div>
                              {/* Parameter Name & Status Pill */}
                              <div className="flex items-start justify-between gap-2 mb-1.5">
                                <span className="font-semibold text-xs text-[#0F172A]">
                                  {param.name}
                                </span>
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 border ${
                                    isConflicting
                                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                                      : isResolved
                                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  }`}
                                >
                                  {isConflicting ? 'CONFLICT' : isResolved ? 'RESOLVED' : 'VERIFIED EVIDENCE'}
                                </span>
                              </div>

                              {/* Parameter Value */}
                              <div className="font-mono text-base font-bold text-[#0F172A] my-2">
                                {fact.value} {fact.unit || ''}
                              </div>
                            </div>

                            {/* Provenance Box */}
                            <div className="mt-3 pt-2.5 border-t border-[#E2E8F0] text-[11px] text-[#64748B] space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-mono text-[#0F172A] font-medium flex items-center gap-1">
                                  <span className="material-symbols-outlined text-xs text-[#1D4ED8]">description</span>
                                  {fact.sourceEvidenceId}
                                </span>
                                <span className="truncate max-w-[140px]" title={fact.sourceFileName}>
                                  {fact.sourceFileName}
                                </span>
                              </div>

                              <div className="flex items-center justify-between font-mono text-[10px]">
                                <span>Loc: {fact.sourceLocation}</span>
                                <span
                                  className="text-slate-600 bg-slate-100 px-1 rounded cursor-pointer"
                                  title={fact.evidenceSha256}
                                  onClick={() => navigator.clipboard.writeText(fact.evidenceSha256)}
                                >
                                  SHA: {truncateHash(fact.evidenceSha256, 4, 4)}
                                </span>
                              </div>

                              {isConflicting && fact.conflictId && (
                                <div className="mt-2 pt-2 border-t border-amber-200 flex justify-end">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      const conf = conflictsList.find((c) => c.conflictId === fact.conflictId);
                                      if (conf) onOpenConflictModal(conf);
                                    }}
                                    className="px-2.5 py-1 bg-amber-600 text-white rounded text-xs font-semibold hover:bg-amber-700 flex items-center gap-1"
                                  >
                                    <span className="material-symbols-outlined text-xs">how_to_reg</span>
                                    Resolve Discrepancy
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
      </div>

      {/* Immutable Audit Trail Drawer */}
      {auditDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setAuditDrawerOpen(false)} />
          <div className="relative w-full max-w-xl bg-white h-full shadow-2xl z-10 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
            <div className="h-16 px-6 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8F9FA]">
              <div className="flex items-center gap-2.5">
                <span className="w-8 h-8 rounded bg-purple-600 text-white flex items-center justify-center font-mono font-bold text-xs shadow-sm">
                  AUD
                </span>
                <div>
                  <h3 className="font-bold text-sm text-[#0F172A]">Product DNA Audit Trail</h3>
                  <span className="text-[10px] font-mono text-[#64748B]">
                    CRYPTOGRAPHIC AUDIT LOG // SHA-256 INTEGRITY
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAuditDrawerOpen(false)}
                className="text-[#64748B] hover:text-[#0F172A] p-1.5 rounded"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-3">
              {auditLog.length === 0 ? (
                <div className="py-12 text-center text-[#64748B]">
                  <span className="material-symbols-outlined text-3xl text-slate-300 block mb-2">history</span>
                  <p className="text-xs font-medium text-[#0F172A]">No audit events logged yet</p>
                  <p className="text-[11px] text-[#94A3B8] mt-0.5">
                    All parameter extractions, mutations, and conflict resolutions will appear here.
                  </p>
                </div>
              ) : (
                auditLog.map((event) => (
                  <div
                    key={event.eventId}
                    className="p-3.5 bg-[#F8F9FA] border border-[#E2E8F0] rounded-lg flex flex-col gap-1.5 text-xs font-mono"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#1D4ED8]">{event.eventId}</span>
                      <span className="text-[10px] text-[#94A3B8]">{event.timestamp}</span>
                    </div>

                    <div className="text-[#0F172A] font-sans font-semibold">
                      {event.parameterName}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] my-1 bg-white p-2 rounded border border-[#E2E8F0]">
                      <div>
                        <span className="text-[#94A3B8] block text-[9px] uppercase">Previous:</span>
                        <span className="text-slate-600 truncate block">{event.previousValue}</span>
                      </div>
                      <div>
                        <span className="text-[#94A3B8] block text-[9px] uppercase">New Value:</span>
                        <span className="text-emerald-700 font-bold truncate block">{event.newValue}</span>
                      </div>
                    </div>

                    <div className="text-[10px] text-[#64748B] font-sans">
                      <span className="font-semibold text-slate-700">Reason: </span>
                      {event.reason}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-[#E2E8F0]">
                      <span>Source: {event.evidenceSource}</span>
                      <span className="text-slate-600 truncate max-w-[120px]" title={event.evidenceHash}>
                        Hash: {truncateHash(event.evidenceHash, 4, 4)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
