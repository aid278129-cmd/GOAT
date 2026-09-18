import React from 'react';

export function DossiersReportsView({ onNavigateJobs }) {
  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
            Statutory Compliance Reports &amp; Filing Dossiers
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Official BIS CRS application packages, statutory gap assessments, and NABL lab requisition packs.
          </p>
        </div>

        <button
          type="button"
          onClick={onNavigateJobs}
          className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 self-start sm:self-auto shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">rule_folder</span>
          Browse Compliance Jobs
        </button>
      </div>

      {/* Main Empty State */}
      <div className="bg-white border border-[#E2E8F0] rounded-lg p-12 text-center shadow-sm">
        <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-3">
          <span className="material-symbols-outlined text-3xl">description</span>
        </div>
        <h3 className="text-base font-semibold text-[#0F172A] mb-1">
          No reports available
        </h3>
        <p className="text-xs text-[#64748B] max-w-md mx-auto mb-5 leading-relaxed">
          Execute a compliance job to automatically generate certified BIS CRS Filing Dossiers, clause-by-clause statutory gap assessments, and NABL laboratory test requisition packs.
        </p>
        <button
          type="button"
          onClick={onNavigateJobs}
          className="px-4 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors inline-flex items-center gap-1.5 shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
          Go to Compliance Jobs
        </button>
      </div>

      {/* Statutory Deliverable Templates Preview */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
            Automated Statutory Deliverables Architecture
          </h2>
          <span className="font-mono text-[11px] text-[#64748B]">
            3 Templates Ready
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="w-8 h-8 rounded bg-blue-50 text-[#1D4ED8] flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">verified</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                Official BIS CRS Filing Dossier
              </h3>
              <p className="text-xs text-[#64748B] leading-relaxed">
                Complete Form VI application bundle with test summaries, technical construction files, and e-filing payloads ready for ManakOnline submission.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Status</span>
              <span className="text-slate-400">AWAITING COMPILATION</span>
            </div>
          </div>

          <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="w-8 h-8 rounded bg-amber-50 text-amber-600 flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">troubleshoot</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                Clause-by-Clause Gap Assessment
              </h3>
              <p className="text-xs text-[#64748B] leading-relaxed">
                Comprehensive engineering audit report highlighting non-conformances, spatial clearance violations, and recommended remediation paths.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Status</span>
              <span className="text-slate-400">AWAITING COMPILATION</span>
            </div>
          </div>

          <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="w-8 h-8 rounded bg-purple-50 text-purple-600 flex items-center justify-center mb-3">
                <span className="material-symbols-outlined text-base">science</span>
              </div>
              <h3 className="text-xs font-bold text-[#0F172A] mb-1">
                NABL Laboratory Test Requisition
              </h3>
              <p className="text-xs text-[#64748B] leading-relaxed">
                Pre-formatted laboratory testing requisition sheets detailing required test standard clauses, sample quantities, and test conditions.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
              <span>Status</span>
              <span className="text-slate-400">AWAITING COMPILATION</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
