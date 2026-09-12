import React from 'react';

export function SideNav({
  currentView,
  onNavigate,
  onNewAnalysis,
  activeProductName,
  assessmentsCount = 0,
  standardsCount = 51,
}) {
  const pipelineSteps = [
    { id: 'input', step: '01', label: 'Product Input', icon: 'upload_file' },
    { id: 'dna', step: '02', label: 'Product DNA', icon: 'fingerprint' },
    { id: 'applicability', step: '03', label: 'BIS Applicability', icon: 'gavel' },
    { id: 'clauses', step: '04', label: 'Standards & Clauses', icon: 'account_tree' },
    { id: 'evidence', step: '05', label: 'Evidence Matrix', icon: 'policy' },
    { id: 'gaps', step: '06', label: 'Compliance Gaps', icon: 'troubleshoot' },
    { id: 'actions', step: '07', label: 'Lab & Actions', icon: 'science' },
    { id: 'passport', step: '08', label: 'Compliance Passport', icon: 'verified' },
  ];

  const secondaryNav = [
    { id: 'dashboard', label: 'Workspace Overview', icon: 'dashboard' },
    { id: 'knowledge', label: 'BIS Standards Catalog', icon: 'menu_book', count: standardsCount },
    { id: 'evaluation', label: 'Controlled Demo (SIH)', icon: 'biotech' },
  ];

  return (
    <aside className="hidden lg:flex flex-col h-screen p-4 border-r border-slate-200 bg-white fixed left-0 top-0 w-64 z-40 select-none shadow-2xs font-sans">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-2 py-2 mb-3">
        <div className="w-8 h-8 bg-slate-900 rounded flex items-center justify-center shrink-0 shadow-2xs">
          <span className="text-white font-mono font-bold text-xs tracking-tight">ZY</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-sm font-bold tracking-tight text-slate-900 leading-tight">Zyntrix</h1>
          <p className="text-[10px] text-slate-400 font-mono uppercase tracking-widest leading-none mt-0.5">
            BIS Compliance Compiler
          </p>
        </div>
      </div>

      {/* Active Product Indicator */}
      <div className="px-2.5 py-2 mb-3 rounded bg-slate-50 border border-slate-200 flex flex-col gap-0.5">
        <span className="text-[9px] font-mono uppercase text-slate-400 font-bold">Active Dossier</span>
        <span className="text-xs font-semibold text-slate-900 truncate" title={activeProductName || 'No Product Active'}>
          {activeProductName || 'No Product Active'}
        </span>
      </div>

      {/* New Analysis CTA Button */}
      <button
        onClick={onNewAnalysis}
        className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold py-2 px-3 rounded flex items-center justify-center gap-2 mb-3 transition cursor-pointer shadow-2xs active:scale-[0.99]"
      >
        <span className="material-symbols-outlined text-[16px]">add</span>
        <span>New Assessment</span>
      </button>

      {/* 8-Step Pipeline Navigation */}
      <nav className="flex flex-col gap-1 overflow-y-auto flex-1 pr-1">
        <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1.5 px-2">
          Compiler Pipeline
        </div>

        {pipelineSteps.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-2.5 px-2.5 py-1.5 text-xs rounded transition cursor-pointer text-left ${
                isActive
                  ? 'font-bold text-slate-900 bg-slate-100 border border-slate-300 shadow-2xs'
                  : 'font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className={`text-[10px] font-mono shrink-0 ${isActive ? 'text-slate-900 font-bold' : 'text-slate-400'}`}>
                {item.step}
              </span>
              <span className={`material-symbols-outlined text-[17px] shrink-0 ${isActive ? 'text-slate-900' : 'text-slate-400'}`}>
                {item.icon}
              </span>
              <span className="truncate flex-1">{item.label}</span>
            </button>
          );
        })}

        {/* Secondary Navigation */}
        <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mt-3 mb-1 px-2 border-t border-slate-100 pt-2">
          Regulatory Workspace
        </div>

        {secondaryNav.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-2.5 px-2.5 py-1.5 text-xs rounded transition cursor-pointer text-left ${
                isActive
                  ? 'font-bold text-slate-900 bg-slate-100 border border-slate-300 shadow-2xs'
                  : 'font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className={`material-symbols-outlined text-[17px] shrink-0 ${isActive ? 'text-slate-900' : 'text-slate-400'}`}>
                {item.icon}
              </span>
              <span className="truncate flex-1">{item.label}</span>
              {item.count !== undefined && (
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Authority Trust Seal */}
      <div className="pt-2 border-t border-slate-200 mt-auto">
        <div className="p-2 rounded bg-slate-50 border border-slate-200 text-[10px] text-slate-500 flex flex-col gap-0.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-800">Compliance Authority</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono">
            0% LLM Compliance Authority &bull; Rule-Based
          </p>
        </div>
      </div>
    </aside>
  );
}
