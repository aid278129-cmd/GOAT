import React from 'react';

export function WorkspaceView({
  onCreateJobClick,
  jobsCount = 0,
  evidenceCount = 0,
  openFindingsCount = 0,
  attestationCount = 0,
}) {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6 font-sans text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
            Operational Dashboard
          </span>
          <h1 className="font-space-grotesk text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Workspace Operations
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Operational triage, active job monitoring, and statutory audit integrity.
          </p>
        </div>

        <button
          type="button"
          onClick={onCreateJobClick}
          className="px-4 py-2.5 text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-xl transition-all flex items-center gap-1.5 self-start sm:self-auto shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
        >
          <span className="material-symbols-outlined text-sm">add</span>
          New Compliance Job
        </button>
      </div>

      {/* 4 KPI Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-medium text-slate-400">Active Jobs</span>
            <span className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">rule_folder</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-space-grotesk text-2xl font-bold text-white">{jobsCount}</span>
            <span className="text-[11px] font-mono text-slate-500 block mt-0.5">
              {jobsCount === 0 ? 'No active jobs' : `${jobsCount} job(s) in registry`}
            </span>
          </div>
        </div>

        <div className="bg-[#0f1422] border border-amber-500/30 rounded-2xl p-4 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-medium text-amber-400">Open Findings</span>
            <span className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-400/30 text-amber-300 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">troubleshoot</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-space-grotesk text-2xl font-bold text-amber-300">{openFindingsCount}</span>
            <span className="text-[11px] font-mono text-slate-500 block mt-0.5">
              {openFindingsCount === 0 ? 'No open gaps' : `${openFindingsCount} item(s) pending`}
            </span>
          </div>
        </div>

        <div className="bg-[#0f1422] border border-emerald-500/30 rounded-2xl p-4 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-medium text-emerald-400">Evidence Records</span>
            <span className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">policy</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-space-grotesk text-2xl font-bold text-emerald-300">{evidenceCount}</span>
            <span className="text-[11px] font-mono text-slate-500 block mt-0.5">
              {evidenceCount === 0 ? 'No evidence uploaded' : `${evidenceCount} records ingested`}
            </span>
          </div>
        </div>

        <div className="bg-[#0f1422] border border-purple-500/30 rounded-2xl p-4 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-medium text-purple-400">Attestations</span>
            <span className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-400/30 text-purple-300 flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">verified</span>
            </span>
          </div>
          <div className="mt-3">
            <span className="font-space-grotesk text-2xl font-bold text-purple-300">{attestationCount}</span>
            <span className="text-[11px] font-mono text-slate-500 block mt-0.5">
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
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Operational Triage Queue
            </h2>
            <span className="font-mono text-[11px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              Queue Clear
            </span>
          </div>

          <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center shadow-xl">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 mx-auto mb-3 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
              <span className="material-symbols-outlined text-2xl">checklist</span>
            </div>
            <h3 className="font-space-grotesk text-sm font-semibold text-white mb-1">
              Operational Queue Clear
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4 leading-relaxed">
              No compliance jobs currently require statutory triage, manual gap attestation, or NABL lab action.
            </p>
            <button
              type="button"
              onClick={onCreateJobClick}
              className="px-4 py-2 text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-xl transition-all inline-flex items-center gap-1.5 shadow-[0_0_12px_rgba(56,189,248,0.25)] cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Create Compliance Job
            </button>
          </div>
        </div>

        {/* Right Col: System Telemetry */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              System Telemetry
            </h2>
            <span className="font-mono text-[11px] text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
              Operational
            </span>
          </div>

          <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-5 flex flex-col gap-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-xs font-medium text-white block">BIS Gazette Feed</span>
                <span className="font-mono text-[10px] text-slate-500">Automated polling</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
                SYNCHRONIZED
              </span>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-xs font-medium text-white block">Vector Spatial Engine</span>
                <span className="font-mono text-[10px] text-slate-500">Babylon.js 3D CAD worker</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
                STANDBY
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-white block">Cryptographic Log</span>
                <span className="font-mono text-[10px] text-slate-500">Audit trail hash engine</span>
              </div>
              <span className="font-mono text-[11px] font-semibold text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-500/30">
                INTACT
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cryptographic Audit Commit Log */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            Cryptographic Audit Commit Log
          </h2>
          <span className="font-mono text-[11px] text-slate-500">
            SHA-256 Ledger
          </span>
        </div>

        <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center shadow-xl">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center text-cyan-400 mx-auto mb-2 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-xl">history_edu</span>
          </div>
          <h3 className="font-space-grotesk text-xs font-semibold text-white mb-0.5">
            No audit records committed yet
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All statutory determinations, clause approvals, and DSC signatures will be cryptographically logged here.
          </p>
        </div>
      </div>
    </div>
  );
}
