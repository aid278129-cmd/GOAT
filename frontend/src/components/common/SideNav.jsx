import React from 'react';

export function SideNav({ currentView, onNavigate, onNewAnalysis, assessmentsCount = 0, standardsCount = 51 }) {
  const navItems = [
    { id: 'templates', step: '01', label: 'Generate Template', icon: 'description' },
    { id: 'overview', step: '02', label: 'Compliance Overview', icon: 'dashboard' },
    { id: 'analyze', step: '03', label: 'Product Input', icon: 'analytics' },
    { id: 'standards', step: '04', label: 'BIS Standards & Gaps', icon: 'gavel' },
    { id: 'assistant', step: '05', label: 'Compliance Copilot', icon: 'smart_toy' },
    { id: 'knowledge', step: '06', label: 'BIS Standards Catalog', icon: 'menu_book' },
  ];

  return (
    <aside className="hidden lg:flex flex-col h-screen p-4 border-r border-slate-200 bg-white fixed left-0 top-0 w-64 z-40 select-none shadow-xs">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-2 py-2 mb-4">
        <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center shrink-0 shadow-xs">
          <span className="text-white font-bold text-xs tracking-tight">ZY</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-sm font-bold tracking-tight text-slate-900 leading-tight">Zyntrix</h1>
          <p className="text-[10px] text-slate-400 uppercase tracking-widest leading-none mt-0.5">
            BIS Compliance Compiler
          </p>
        </div>
      </div>

      {/* New Analysis CTA Button */}
      <button
        onClick={onNewAnalysis}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2.5 px-3 rounded-lg flex items-center justify-center gap-2 mb-4 transition-all shadow-xs cursor-pointer active:scale-[0.99]"
      >
        <span className="material-symbols-outlined text-[16px]">add</span>
        <span>New Assessment</span>
      </button>

      {/* Workflow Navigation */}
      <nav className="flex flex-col gap-1 overflow-y-auto flex-1 pr-1">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 px-2">
          Compliance Workflow
        </div>

        {navItems.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-3 px-3 py-2 text-xs rounded-lg transition-all cursor-pointer text-left ${
                isActive
                  ? 'font-semibold text-indigo-600 bg-indigo-50/70 border border-indigo-100 shadow-2xs'
                  : 'font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className={`text-[10px] font-mono shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`}>
                {item.step}
              </span>
              <span className={`material-symbols-outlined text-[18px] shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`}>
                {item.icon}
              </span>
              <span className="truncate flex-1">{item.label}</span>
              {item.id === 'knowledge' && (
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {standardsCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom SIH Provenance Badge */}
      <div className="pt-3 border-t border-slate-100 mt-auto">
        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-500 flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-700">Compliance Engine</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            51 Verified BIS Gazette Standards &bull; Real-Time Index
          </p>
        </div>
      </div>
    </aside>
  );
}
