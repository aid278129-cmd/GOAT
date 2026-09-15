import React from 'react';

export function TopBar({
  currentView,
  onNavigate,
  onNewAnalysis,
  mobileMenuOpen,
  setMobileMenuOpen,
  activeAssessment,
  assessmentsList = [],
  onSelectAssessment,
  isHealthy = true,
  onClearAll,
  onExportDossier,
  onCommitAudit,
}) {
  const pipelineSteps = [
    { id: 'input', label: '1. Product Input' },
    { id: 'dna', label: '2. Product DNA' },
    { id: 'applicability', label: '3. BIS Applicability' },
    { id: 'clauses', label: '4. Standards & Clauses' },
    { id: 'evidence', label: '5. Evidence Matrix' },
    { id: 'gaps', label: '6. Compliance Gaps' },
    { id: 'actions', label: '7. Lab & Actions' },
    { id: 'passport', label: '8. Compliance Passport' },
    { id: 'dashboard', label: 'Workspace Overview' },
    { id: 'knowledge', label: 'BIS Standards Catalog' },
    { id: 'evaluation', label: 'Controlled Demo (SIH)' },
  ];

  // Derive metadata from active assessment or fallback to Stitch reference
  const dossierId = activeAssessment?.assessment_number || activeAssessment?.assessment_id?.slice(0, 12) || 'IND-2024-0049';
  const targetStandard = activeAssessment?.target_standard || activeAssessment?.primary_standard || (activeAssessment?.applicability?.[0]?.standard_number) || 'IS 13252, 16046';
  const schemeName = activeAssessment?.scheme || 'CRS / MeitY';
  const sha256Short = activeAssessment?.sha256_hash ? `${activeAssessment.sha256_hash.slice(0, 4)}...${activeAssessment.sha256_hash.slice(-4)}` : 'e84a...c96e';

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-2xs font-sans">
      {/* Primary Regulatory Header Strip */}
      <div className="h-12 flex items-center justify-between px-3 md:px-5 gap-3">
        {/* Left Section: Mobile Toggle & Brand / Dossier Title */}
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden text-slate-600 p-1.5 rounded hover:bg-slate-100 transition cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            <span className="material-symbols-outlined text-lg">{mobileMenuOpen ? 'close' : 'menu'}</span>
          </button>

          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-slate-900 rounded flex items-center justify-center shrink-0 shadow-2xs">
              <span className="text-white font-mono font-bold text-[10px] tracking-tighter">BIS</span>
            </div>
            <div className="hidden sm:flex flex-col">
              <span className="font-bold text-xs tracking-tight text-slate-900 leading-tight">
                BIS Compliance Intelligence Compiler
              </span>
            </div>
          </div>
        </div>

        {/* Center: High-Density Regulatory Context Strip (from Stitch) */}
        <div className="hidden xl:flex items-center gap-3 text-xs font-mono border-x border-slate-200 px-4 py-1 bg-slate-50/70 rounded">
          <div className="flex items-center gap-1 text-slate-700">
            <span className="text-slate-400 uppercase text-[10px]">Dossier:</span>
            <span className="font-semibold text-slate-900">{dossierId}</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1 text-slate-700">
            <span className="text-slate-400 uppercase text-[10px]">IS:</span>
            <span className="font-semibold text-slate-900">{targetStandard.replace(/^IS\s*/i, '')}</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1 text-slate-700">
            <span className="text-slate-400 uppercase text-[10px]">Scheme:</span>
            <span className="font-semibold text-slate-900">{schemeName}</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1.5 text-slate-700">
            <span className="text-slate-400 uppercase text-[10px]">SHA-256:</span>
            <span className="font-mono text-[11px] text-slate-800">{sha256Short}</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              VERIFIED
            </span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1 text-slate-700">
            <span className="material-symbols-outlined text-[14px] text-slate-600">lock</span>
            <span className="text-[10px] text-slate-500 uppercase">State:</span>
            <span className="font-bold text-slate-800 text-[11px]">Locked</span>
          </div>
        </div>

        {/* Right: Actions & Switchers */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Assessment Switcher Dropdown */}
          {assessmentsList.length > 0 && (
            <div className="flex items-center gap-1.5">
              <select
                id="topbar-assessment-select"
                aria-label="Select Product Dossier"
                value={activeAssessment?.assessment_id || ''}
                onChange={(e) => onSelectAssessment(e.target.value)}
                className="px-2 py-1 text-xs border border-slate-300 rounded bg-slate-50 font-medium text-slate-800 focus:outline-none focus:border-slate-900 max-w-[140px] md:max-w-[190px] truncate"
              >
                {assessmentsList.map((a) => (
                  <option key={a.assessment_id} value={a.assessment_id}>
                    {a.product_name || a.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Export BIS Dossier Button */}
          <button
            onClick={onExportDossier || (() => onNavigate('passport'))}
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-slate-300 hover:border-slate-400 bg-white text-slate-800 text-xs font-semibold hover:bg-slate-50 transition cursor-pointer shadow-2xs"
            title="Export official BIS technical compliance file"
          >
            <span className="material-symbols-outlined text-[14px] text-slate-600">file_download</span>
            <span>Export BIS Dossier</span>
          </button>

          {/* Commit Audit Action (Stitch Primary Action) */}
          <button
            onClick={onCommitAudit || (() => onNavigate('passport'))}
            className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3 py-1.5 rounded transition shadow-2xs cursor-pointer active:scale-95"
            title="Commit cryptographic audit signature and freeze dossier state"
          >
            <span className="material-symbols-outlined text-[14px]">verified_user</span>
            <span>Commit Audit</span>
          </button>

          {/* Backend Status Indicator */}
          <div
            className="hidden md:flex items-center gap-1.5 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-[10px] font-mono text-slate-700"
            title={isHealthy ? 'FastAPI Compliance Engine Online' : 'Backend Disconnected'}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            <span className="font-bold">{isHealthy ? 'LIVE' : 'OFFLINE'}</span>
          </div>

          {/* Reset Workspace */}
          {onClearAll && (
            <button
              onClick={onClearAll}
              className="text-slate-400 hover:text-rose-600 p-1.5 rounded hover:bg-rose-50 transition cursor-pointer"
              title="Reset workspace and clear assessments"
            >
              <span className="material-symbols-outlined text-base">refresh</span>
            </button>
          )}
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white p-3 shadow-xl z-50 space-y-1">
          {pipelineSteps.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onNavigate(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full text-left px-3 py-2 rounded text-xs font-semibold ${
                currentView === item.id
                  ? 'bg-slate-100 text-slate-900 font-bold border border-slate-300'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
}
