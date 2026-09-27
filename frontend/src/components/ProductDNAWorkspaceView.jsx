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
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-[11px] font-mono font-medium mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            ACCEPTED EVIDENCE → STRUCTURED PRODUCT DNA
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
            Structured Product DNA &amp; Provenance Workstation
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Deterministic technical parameters derived strictly from Accepted Evidence artifacts.
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setAuditDrawerOpen(true)}
            className="px-3.5 py-2 text-xs font-medium text-slate-300 bg-slate-900 border border-slate-700/80 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">history</span>
            Audit Trail ({auditLog.length})
          </button>
          <button
            type="button"
            onClick={onOpenExtractModal}
            className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-cyan-500/20 cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm font-bold">add_link</span>
            Extract Verified Parameter
          </button>
        </div>
      </div>

      {/* Regulatory Boundary Firewall Notice */}
      <div className="p-4 bg-[#0f1422]/90 text-slate-100 rounded-xl flex items-start gap-3 shadow-xl border border-slate-800">
        <span className="material-symbols-outlined text-cyan-400 text-xl mt-0.5">hub</span>
        <div className="flex-1 text-xs">
          <span className="font-mono font-bold text-cyan-300 block mb-0.5 uppercase tracking-wider text-[11px]">
            Statutory Pipeline Invariant: Provenance Chain
          </span>
          <p className="text-slate-300 leading-relaxed text-[11px]">
            <span className="font-mono text-cyan-400 font-semibold">Evidence (Accepted)</span> →{' '}
            <span className="font-mono text-cyan-400 font-semibold">Product DNA</span> →{' '}
            <span className="font-mono text-cyan-400 font-semibold">Engineering Assessment</span> →{' '}
            <span className="font-mono text-cyan-400 font-semibold">Human Attestation</span> →{' '}
            <span className="font-mono text-cyan-400 font-semibold">BIS Submission</span>.
            Product DNA parameters represent empirical characteristics. No parameter is automatically marked as <span className="font-mono text-slate-500">PASS</span>, <span className="font-mono text-slate-500">COMPLIANT</span>, or <span className="font-mono text-slate-500">CERTIFIED</span>.
          </p>
        </div>
      </div>

      {/* Active Conflict Warning Banner */}
      {activeConflicts.length > 0 && (
        <div className="p-4 bg-amber-950/40 border border-amber-800/80 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xl animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-amber-950/80 border border-amber-800/80 text-amber-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-base">warning</span>
            </span>
            <div>
              <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider font-mono font-['Space_Grotesk']">
                {activeConflicts.length} Parameter Conflict{activeConflicts.length > 1 ? 's' : ''} Require Human Resolution
              </h4>
              <p className="text-xs text-amber-200/80 mt-0.5">
                Multiple accepted evidence sources specify differing values. Autonomous resolution is barred.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onOpenConflictModal(activeConflicts[0])}
            className="px-3.5 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 text-xs font-semibold rounded-lg transition-all self-start sm:self-auto shadow-md shadow-amber-500/20 flex items-center gap-1.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">how_to_reg</span>
            Resolve Conflict ({activeConflicts[0].parameterName})
          </button>
        </div>
      )}

      {/* Stats Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Verified Parameters</span>
          <span className="font-mono text-xl font-bold text-slate-100 mt-1 block">
            {populatedFactsCount} / {CANONICAL_PARAMETERS.length}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Accepted Backing Artifacts</span>
          <span className="font-mono text-xl font-bold text-emerald-400 mt-1 block">
            {new Set(Object.values(productDnaFacts).map((f) => f.sourceEvidenceId).filter(Boolean)).size}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Active Parameter Conflicts</span>
          <span className="font-mono text-xl font-bold text-amber-400 mt-1 block">
            {activeConflicts.length}
          </span>
        </div>

        <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-4 shadow-xl">
          <span className="text-[11px] text-slate-400 block font-medium">Audit Trail Events</span>
          <span className="font-mono text-xl font-bold text-purple-400 mt-1 block">
            {auditLog.length}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-3 flex flex-col md:flex-row items-center justify-between gap-3 shadow-xl">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar w-full md:w-auto">
          <button
            type="button"
            onClick={() => setSelectedSection('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
              selectedSection === 'ALL'
                ? 'bg-cyan-500 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Sections
          </button>
          {sectionsList.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => setSelectedSection(sec.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                selectedSection === sec.id
                  ? 'bg-cyan-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {sec.title}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <span className="material-symbols-outlined text-sm text-slate-500 absolute left-3 top-2.5">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search parameter, source, or value..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Structured Product DNA Sections */}
      <div className="flex flex-col gap-6">
        {sectionsList
          .filter((sec) => selectedSection === 'ALL' || selectedSection === sec.id)
          .map((sec) => {
            const sectionParams = CANONICAL_PARAMETERS.filter((p) => p.section === sec.id);
            const populatedInSection = sectionParams.filter(
              (p) => productDnaFacts[p.id]?.value !== undefined && productDnaFacts[p.id]?.value !== null
            );

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
                className="bg-[#0f1422]/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col"
              >
                {/* Section Header */}
                <div className="px-5 py-3.5 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-cyan-400 text-base">
                      {sec.icon}
                    </span>
                    <div>
                      <h3 className="font-bold text-xs text-slate-100 uppercase tracking-wider font-mono font-['Space_Grotesk']">
                        {sec.title}
                      </h3>
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        {sec.description}
                      </span>
                    </div>
                  </div>
                  <span className="font-mono text-xs text-slate-300 bg-slate-900 px-2.5 py-0.5 rounded-full border border-slate-700">
                    {populatedInSection.length} / {sectionParams.length} Parameters
                  </span>
                </div>

                {/* Section Content */}
                <div className="p-5">
                  {populatedInSection.length === 0 ? (
                    <div className="py-8 px-4 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/40">
                      <span className="material-symbols-outlined text-2xl text-slate-500 mb-1 block">
                        fact_check
                      </span>
                      <h4 className="text-xs font-semibold text-slate-200 font-['Space_Grotesk'] mb-0.5">
                        No verified parameters available.
                      </h4>
                      <p className="text-[11px] text-slate-400 max-w-sm mx-auto mb-3">
                        Parameters in {sec.title} will populate only when evidence artifacts are reviewed and ACCEPTED by an engineer.
                      </p>
                      <button
                        type="button"
                        onClick={onOpenExtractModal}
                        className="px-3.5 py-1.5 text-xs text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 font-medium rounded-lg transition-colors inline-flex items-center gap-1.5 cursor-pointer shadow-sm"
                      >
                        <span className="material-symbols-outlined text-xs">add_link</span>
                        Extract Parameter
                      </button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {visibleParams.map((param) => {
                        const fact = productDnaFacts[param.id];
                        const isConflicting = fact.reviewStatus === ParameterReviewStatus.CONFLICTING;
                        const isResolved = fact.reviewStatus === ParameterReviewStatus.ENGINEER_RESOLVED;

                        return (
                          <div
                            key={param.id}
                            className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                              isConflicting
                                ? 'border-amber-500/60 bg-amber-950/20 shadow-inner'
                                : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                            }`}
                          >
                            <div>
                              <div className="flex items-start justify-between gap-2 mb-1.5">
                                <span className="font-semibold text-xs text-slate-200 font-['Space_Grotesk']">
                                  {param.name}
                                </span>
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 border ${
                                    isConflicting
                                      ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                                      : isResolved
                                      ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                                      : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                                  }`}
                                >
                                  {isConflicting ? 'CONFLICT' : isResolved ? 'RESOLVED' : 'VERIFIED EVIDENCE'}
                                </span>
                              </div>

                              <div className="font-mono text-base font-bold text-slate-100 my-2">
                                {fact.value} {fact.unit || ''}
                              </div>
                            </div>

                            <div className="mt-3 pt-2.5 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-mono text-cyan-400 font-medium flex items-center gap-1">
                                  <span className="material-symbols-outlined text-xs text-cyan-400">description</span>
                                  {fact.sourceEvidenceId}
                                </span>
                                <span className="truncate max-w-[140px] text-slate-300" title={fact.sourceFileName}>
                                  {fact.sourceFileName}
                                </span>
                              </div>

                              <div className="flex items-center justify-between font-mono text-[10px]">
                                <span>Loc: {fact.sourceLocation}</span>
                                <span
                                  className="text-cyan-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 cursor-pointer hover:border-cyan-500"
                                  title={fact.evidenceSha256}
                                  onClick={() => navigator.clipboard.writeText(fact.evidenceSha256)}
                                >
                                  SHA: {truncateHash(fact.evidenceSha256, 4, 4)}
                                </span>
                              </div>

                              {isConflicting && fact.conflictId && (
                                <div className="mt-2 pt-2 border-t border-amber-900/60 flex justify-end">
                                  <button
                                    type="button"
                                    onClick={() => {
                                      const conf = conflictsList.find((c) => c.conflictId === fact.conflictId);
                                      if (conf) onOpenConflictModal(conf);
                                    }}
                                    className="px-2.5 py-1 bg-amber-600 text-slate-950 font-semibold rounded-lg text-xs hover:bg-amber-500 flex items-center gap-1 cursor-pointer"
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
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setAuditDrawerOpen(false)} />
          <div className="relative w-full max-w-xl bg-[#0b0f19] text-slate-100 h-full shadow-2xl z-10 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200 border-l border-slate-800">
            <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center gap-2.5">
                <span className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/60 text-purple-400 flex items-center justify-center font-mono font-bold text-xs shadow-sm">
                  AUD
                </span>
                <div>
                  <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">Product DNA Audit Trail</h3>
                  <span className="text-[10px] font-mono text-cyan-400 tracking-wider">
                    CRYPTOGRAPHIC AUDIT LOG // SHA-256 INTEGRITY
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAuditDrawerOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-3">
              {auditLog.length === 0 ? (
                <div className="py-12 text-center text-slate-400">
                  <span className="material-symbols-outlined text-3xl text-slate-600 block mb-2">history</span>
                  <p className="text-xs font-medium text-slate-200 font-['Space_Grotesk']">No audit events logged yet</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    All parameter extractions, mutations, and conflict resolutions will appear here.
                  </p>
                </div>
              ) : (
                auditLog.map((event) => (
                  <div
                    key={event.eventId}
                    className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-col gap-1.5 text-xs font-mono"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-cyan-400">{event.eventId}</span>
                      <span className="text-[10px] text-slate-500">{event.timestamp}</span>
                    </div>

                    <div className="text-slate-200 font-sans font-semibold">
                      {event.parameterName}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] my-1 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase tracking-wider">Previous:</span>
                        <span className="text-slate-400 truncate block">{event.previousValue}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase tracking-wider">New Value:</span>
                        <span className="text-emerald-400 font-bold truncate block">{event.newValue}</span>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 font-sans">
                      <span className="font-semibold text-slate-300">Reason: </span>
                      {event.reason}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800">
                      <span>Source: {event.evidenceSource}</span>
                      <span className="text-cyan-400 truncate max-w-[120px]" title={event.evidenceHash}>
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
