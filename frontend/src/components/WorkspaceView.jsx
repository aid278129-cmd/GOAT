import React from 'react';

export function WorkspaceView({
  onCreateJobClick,
  jobsCount = 0,
  evidenceCount = 0,
  openFindingsCount = 0,
  attestationCount = 0,
}) {
  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
            Workspace Operations
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Operational triage, active job monitoring, and statutory audit integrity.
          </p>
        </div>

        <button
          type="button"
          onClick={onCreateJobClick}
          className="px-3.5 py-2 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 self-start sm:self-auto shadow-sm"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          New Compliance Job
        </button>
      </div>

      {/* 4 KPI Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#64748B]">Active Jobs</span>
            <span className="w-6 h-6 rounded bg-blue-50 text-[#1D4ED8] flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">rule_folder</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-mono text-2xl font-bold text-[#0F172A]">{jobsCount}</span>
            <span className="text-[11px] text-[#94A3B8] block mt-0.5">
              {jobsCount === 0 ? 'No active jobs' : `${jobsCount} job(s) in registry`}
            </span>
          </div>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#64748B]">Open Findings</span>
            <span className="w-6 h-6 rounded bg-amber-50 text-amber-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">troubleshoot</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-mono text-2xl font-bold text-[#0F172A]">{openFindingsCount}</span>
            <span className="text-[11px] text-[#94A3B8] block mt-0.5">
              {openFindingsCount === 0 ? 'No open gaps' : `${openFindingsCount} item(s) pending`}
            </span>
          </div>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#64748B]">Evidence Records</span>
            <span className="w-6 h-6 rounded bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">policy</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-mono text-2xl font-bold text-[#0F172A]">{evidenceCount}</span>
            <span className="text-[11px] text-[#94A3B8] block mt-0.5">
              {evidenceCount === 0 ? 'No evidence uploaded' : `${evidenceCount} records ingested`}
            </span>
          </div>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[#64748B]">Attestations</span>
            <span className="w-6 h-6 rounded bg-purple-50 text-purple-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">verified</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-mono text-2xl font-bold text-[#0F172A]">{attestationCount}</span>
            <span className="text-[11px] text-[#94A3B8] block mt-0.5">
              {attestationCount === 0 ? 'No attestations signed' : `${attestationCount} signed attestations`}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Triage Queue & System Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Operational Triage Queue */}
        <div className="lg:col-span-2 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
              Operational Triage Queue
            </h2>
            <span className="font-mono text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Queue Clear
            </span>
          </div>

          <div className="bg-white border border-[#E2E8F0] rounded-lg p-8 text-center shadow-sm">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-3">
              <span className="material-symbols-outlined text-2xl">checklist</span>
            </div>
            <h3 className="text-sm font-semibold text-[#0F172A] mb-1">
              Operational Queue Clear
            </h3>
            <p className="text-xs text-[#64748B] max-w-sm mx-auto mb-4 leading-relaxed">
              No compliance jobs currently require statutory triage, manual gap attestation, or NABL lab action.
            </p>
            <button
              type="button"
              onClick={onCreateJobClick}
              className="px-3 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors inline-flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Create Compliance Job
            </button>
          </div>
        </div>

        {/* Right Col: System Telemetry */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
              System Telemetry
            </h2>
            <span className="font-mono text-[11px] text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              Operational
            </span>
          </div>

          <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 flex flex-col gap-4 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div>
                <span className="text-xs font-medium text-[#0F172A] block">BIS Gazette Feed</span>
                <span className="font-mono text-[10px] text-[#64748B]">Automated polling</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                SYNCHRONIZED
              </span>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
              <div>
                <span className="text-xs font-medium text-[#0F172A] block">Vector Spatial Engine</span>
                <span className="font-mono text-[10px] text-[#64748B]">Babylon.js 3D worker</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                STANDBY
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-[#0F172A] block">Cryptographic Log</span>
                <span className="font-mono text-[10px] text-[#64748B]">Audit trail hash engine</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded">
                INTEACT
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cryptographic Audit Commit Log (Empty State) */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#0F172A] font-mono">
            Cryptographic Audit Commit Log
          </h2>
          <span className="font-mono text-[11px] text-[#64748B]">
            SHA-256 Ledger
          </span>
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-8 text-center shadow-sm">
          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-[#94A3B8] mx-auto mb-2">
            <span className="material-symbols-outlined text-xl">history_edu</span>
          </div>
          <h3 className="text-xs font-semibold text-[#0F172A] mb-0.5">
            No audit records committed yet
          </h3>
          <p className="text-xs text-[#64748B] max-w-sm mx-auto">
            All statutory determinations, clause approvals, and DSC signatures will be cryptographically logged here.
          </p>
        </div>
      </div>
    </div>
  );
}
