import React from 'react';

export function SideNav({
  currentView,
  onNavigate,
  onNewAnalysis,
  activeProductName,
  assessmentsCount = 0,
  standardsCount = 51,
  onExecuteIntegrityCheck,
  stats = {},
}) {
  // Extract or default dynamic badges to match Stitch Regulatory Matrix
  const dnaCount = stats.dnaCount || '16 OK';
  const standardsCountBadge = stats.standardsCountBadge || '2 STDs';
  const clausesCountBadge = stats.clausesCountBadge || '38 CLAUSES';
  const evidenceCountBadge = stats.evidenceCountBadge || '36 VER';
  const gapsCountBadge = stats.gapsCountBadge || '2 GAP';
  const actionsCountBadge = stats.actionsCountBadge || '3 ACT';
  const passportBadge = stats.passportBadge || 'PASS';

  const pipelineSteps = [
    { id: 'input', step: '01', label: '1. Product Input', icon: 'upload_file', badge: '173' },
    { id: 'dna', step: '02', label: '2. Product DNA', icon: 'fingerprint', badge: dnaCount, badgeType: 'info' },
    { id: 'applicability', step: '03', label: '3. BIS Applicability', icon: 'gavel', badge: standardsCountBadge, badgeType: 'info' },
    { id: 'clauses', step: '04', label: '4. Standards & Clauses', icon: 'account_tree', badge: clausesCountBadge, badgeType: 'primary' },
    { id: 'evidence', step: '05', label: '5. Evidence Matrix', icon: 'policy', badge: evidenceCountBadge, badgeType: 'info' },
    { id: 'gaps', step: '06', label: '6. Compliance Gaps', icon: 'troubleshoot', badge: gapsCountBadge, badgeType: 'danger' },
    { id: 'actions', step: '07', label: '7. Lab & Actions', icon: 'science', badge: actionsCountBadge, badgeType: 'warning' },
    { id: 'passport', step: '08', label: '8. Compliance Passport', icon: 'verified', badge: passportBadge, badgeType: 'success' },
  ];

  const secondaryNav = [
    { id: 'dashboard', label: 'Workspace Overview', icon: 'dashboard' },
    { id: 'knowledge', label: 'BIS Standards Catalog', icon: 'menu_book', count: standardsCount },
    { id: 'evaluation', label: 'Controlled Demo (SIH)', icon: 'biotech' },
  ];

  return (
    <aside className="hidden lg:flex flex-col h-screen p-3.5 border-r border-slate-200 bg-white fixed left-0 top-0 w-64 z-40 select-none shadow-2xs font-sans">
      {/* Brand Header */}
      <div className="flex items-center gap-2.5 px-2 py-2 mb-2 border-b border-slate-100 pb-3">
        <div className="w-8 h-8 bg-slate-900 rounded flex items-center justify-center shrink-0 shadow-2xs">
          <span className="text-white font-mono font-bold text-xs tracking-tighter">BIS</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-xs font-bold tracking-tight text-slate-900 leading-tight uppercase">
            BIS Compliance
          </h1>
          <p className="text-[10px] text-slate-500 font-mono tracking-tight leading-none mt-0.5">
            Intelligence Compiler
          </p>
        </div>
      </div>

      {/* Compiler Pipeline Sub-Header */}
      <div className="px-2 mb-2 flex items-center justify-between">
        <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-400">
          Compiler Pipeline
        </span>
        <span className="text-[9px] font-mono text-slate-400">v1.4</span>
      </div>

      {/* Active Product Indicator */}
      <div className="px-2.5 py-1.5 mb-2.5 rounded bg-slate-50 border border-slate-200 flex flex-col gap-0.5">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-mono uppercase text-slate-400 font-bold">Active Dossier</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Active"></span>
        </div>
        <span className="text-xs font-semibold text-slate-900 truncate" title={activeProductName || 'No Product Active'}>
          {activeProductName || 'Industrial Edge Gateway (SMPS-500W)'}
        </span>
      </div>

      {/* 8-Step Pipeline Navigation (Stitch Layout) */}
      <nav className="flex flex-col gap-0.5 overflow-y-auto flex-1 pr-0.5">
        {pipelineSteps.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center justify-between px-2 py-1.5 text-xs rounded transition cursor-pointer text-left ${
                isActive
                  ? 'font-bold text-white bg-slate-900 shadow-2xs'
                  : 'font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <span className={`text-[10px] font-mono shrink-0 ${isActive ? 'text-slate-300' : 'text-slate-400'}`}>
                  {item.step}
                </span>
                <span className="truncate">{item.label}</span>
              </div>

              {/* Status Badge Pills */}
              {item.badge && (
                <span
                  className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded shrink-0 ml-1.5 ${
                    isActive
                      ? 'bg-slate-800 text-white border border-slate-700'
                      : item.badgeType === 'danger'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : item.badgeType === 'warning'
                      ? 'bg-amber-50 text-amber-800 border border-amber-200'
                      : item.badgeType === 'success'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Action: Execute Integrity Check Button */}
        <div className="pt-2 pb-1">
          <button
            onClick={onExecuteIntegrityCheck}
            className="w-full bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-semibold py-1.5 px-2 rounded flex items-center justify-center gap-1.5 transition cursor-pointer shadow-2xs active:scale-[0.99]"
          >
            <span className="material-symbols-outlined text-[15px]">verified</span>
            <span>Execute Integrity Check</span>
          </button>
        </div>

        {/* Secondary Navigation */}
        <div className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider mt-2 mb-1 px-2 border-t border-slate-100 pt-2">
          Regulatory Workspace
        </div>

        {secondaryNav.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center justify-between px-2 py-1.5 text-xs rounded transition cursor-pointer text-left ${
                isActive
                  ? 'font-bold text-slate-900 bg-slate-100 border border-slate-300 shadow-2xs'
                  : 'font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <span className={`material-symbols-outlined text-[16px] shrink-0 ${isActive ? 'text-slate-900' : 'text-slate-400'}`}>
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </div>
              {item.count !== undefined && (
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Diagnostics Strip (from Stitch) */}
      <div className="pt-2 border-t border-slate-200 mt-auto flex flex-col gap-1 text-[10px] font-mono text-slate-500">
        <div className="flex items-center justify-between px-1">
          <span className="hover:text-slate-800 cursor-pointer">Audit Settings</span>
          <span className="hover:text-slate-800 cursor-pointer">System Diagnostics</span>
        </div>
        <div className="px-1 pt-1 border-t border-slate-100 flex items-center justify-between text-[9px] text-slate-400">
          <span>CRS Core 2024.1</span>
          <span className="text-emerald-700 font-semibold">Deterministic</span>
        </div>
      </div>
    </aside>
  );
}
