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

  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-30 shadow-2xs font-sans">
      {/* Left: Mobile Toggle & Product Dossier Selector */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden text-slate-500 p-1.5 rounded hover:bg-slate-50 hover:text-slate-900 transition cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <span className="material-symbols-outlined text-lg">{mobileMenuOpen ? 'close' : 'menu'}</span>
        </button>

        <div className="flex lg:hidden items-center gap-2">
          <div className="w-6 h-6 bg-slate-900 rounded flex items-center justify-center shrink-0">
            <span className="text-white font-mono font-bold text-[10px]">ZY</span>
          </div>
          <span className="font-bold text-xs text-slate-900">Zyntrix</span>
        </div>

        {/* Assessment Switcher Dropdown */}
        {assessmentsList.length > 0 ? (
          <div className="flex items-center gap-2">
            <label htmlFor="assessment-select" className="hidden sm:inline text-[11px] font-mono text-slate-400 uppercase">
              Dossier:
            </label>
            <select
              id="assessment-select"
              value={activeAssessment?.assessment_id || ''}
              onChange={(e) => onSelectAssessment(e.target.value)}
              className="px-2.5 py-1 text-xs border border-slate-300 rounded bg-slate-50 font-medium text-slate-800 focus:outline-none focus:border-slate-900 max-w-[220px] md:max-w-[320px] truncate"
            >
              {assessmentsList.map((a) => (
                <option key={a.assessment_id} value={a.assessment_id}>
                  {a.product_name || a.title} ({a.assessment_number || a.assessment_id?.slice(0, 6)})
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-0.5 bg-slate-100 rounded text-xs text-slate-500 font-mono">
            <span>No Active Product Dossier</span>
          </div>
        )}
      </div>

      {/* Right: Controls & Status */}
      <div className="flex items-center gap-2.5">
        {/* Backend Online Indicator */}
        <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 border border-slate-200 rounded text-[10px] font-mono text-slate-700">
          <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          <span className="hidden sm:inline">Backend:</span>
          <span className="font-bold">{isHealthy ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        {/* Clear All Data */}
        {onClearAll && (
          <button
            onClick={onClearAll}
            className="hidden md:flex items-center gap-1 px-2.5 py-1 rounded text-xs text-slate-500 hover:text-rose-700 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 transition cursor-pointer"
            title="Reset workspace and clear assessments"
          >
            <span className="material-symbols-outlined text-[14px]">refresh</span>
            <span>Reset</span>
          </button>
        )}

        {/* New Product CTA */}
        <button
          onClick={onNewAnalysis}
          className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3 py-1.5 rounded flex items-center gap-1 transition shadow-2xs cursor-pointer active:scale-95"
        >
          <span className="material-symbols-outlined text-[14px]">add</span>
          <span>New Product</span>
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-x-0 top-14 bg-white border-b border-slate-200 p-4 shadow-xl z-50 space-y-1">
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
