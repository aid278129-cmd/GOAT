import React from 'react';

/**
 * SideNav
 * 
 * Compact vertical workstation navigation for GOAT BIS Compliance Compiler.
 * Primary:
 *   COMPLIANCE COMPILER
 *   01 Product
 *   02 Applicability
 *   03 Requirements
 *   04 Evidence
 *   05 Gaps
 *   06 Actions
 *   07 Assessment
 * Divider
 * Secondary:
 *   Assistant
 *   Jobs
 *   Workspace
 *   Review
 *   Knowledge Base
 *   Settings
 */

export const GOLDEN_PATH_NAV = [
  { id: 'dna', step: '01', title: 'Product DNA', icon: 'fingerprint' },
  { id: 'applicability', step: '02', title: 'Applicability', icon: 'verified' },
  { id: 'standards', step: '03', title: 'Requirements', icon: 'rule' },
  { id: 'evidence', step: '04', title: 'Evidence Matrix', icon: 'policy' },
  { id: 'gaps', step: '05', title: 'Gap Engine', icon: 'rule_folder' },
  { id: 'lab', step: '06', title: 'Lab Dispatch', icon: 'science' },
  { id: 'passport', step: '07', title: 'Passport', icon: 'verified_user' },
];

export const SECONDARY_NAV = [
  { id: 'copilot', title: 'GOAT Copilot', icon: 'smart_toy', isAction: true },
  { id: 'jobs', title: 'Jobs Directory', icon: 'inventory_2' },
  { id: 'workspace', title: 'Workspace', icon: 'dashboard' },
  { id: 'reviews', title: 'Attestation & Review', icon: 'rate_review' },
  { id: 'workstation', title: 'Knowledge Base', icon: 'auto_stories' },
  { id: 'settings', title: 'System Settings', icon: 'settings' },
];

export const NAV_ITEMS = [
  ...GOLDEN_PATH_NAV,
  ...SECONDARY_NAV,
];

export function SideNav({
  activeTab,
  onSelectTab,
  onToggleCopilot,
  isCopilotOpen = false,
  mobileOpen,
  onCloseMobile
}) {
  const navContent = (
    <div className="flex flex-col justify-between h-full bg-[#0b0f19] text-slate-200 font-sans overflow-y-auto border-r border-slate-800/80">
      {/* Brand & Navigation */}
      <div className="flex flex-col">
        {/* Top Brand Block */}
        <div className="h-14 px-5 flex items-center justify-between border-b border-slate-800/80 shrink-0 bg-[#080c15]">
          <button 
            type="button"
            onClick={() => onSelectTab('home')}
            className="flex items-center gap-2.5 text-left cursor-pointer group"
            title="Return to 3D Homepage"
          >
            <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_12px_rgba(56,189,248,0.25)] group-hover:border-cyan-300 group-hover:scale-105 transition-all">
              <span className="material-symbols-outlined text-[16px]">verified</span>
            </div>
            <div>
              <span className="font-space-grotesk font-bold text-xs tracking-wider text-white uppercase block leading-tight">
                GOAT <span className="text-cyan-400 font-mono text-[9px]">v2.6</span>
              </span>
              <span className="text-[10px] text-cyan-300/60 block leading-tight font-mono tracking-tight">
                BIS Compliance Compiler
              </span>
            </div>
          </button>
        </div>

        {/* Primary Compiler Workflow */}
        <div className="px-3 pt-3 pb-2">
          {/* 3D Homepage Button */}
          <button
            type="button"
            onClick={() => {
              onSelectTab('home');
              if (onCloseMobile) onCloseMobile();
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 mb-2 rounded-lg text-xs font-medium transition-all text-left cursor-pointer border ${
              activeTab === 'home'
                ? 'text-cyan-300 bg-cyan-950/40 border-cyan-500/40 font-bold shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                : 'text-slate-400 bg-slate-900/50 border-slate-800/80 hover:text-cyan-200 hover:border-cyan-500/30 hover:bg-slate-800/60'
            }`}
          >
            <span className="material-symbols-outlined text-[18px] text-cyan-400">
              home
            </span>
            <span className="truncate font-space-grotesk font-semibold tracking-wide">3D Homepage</span>
          </button>

          <div className="px-2 pt-1 pb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
              Compiler Pipeline
            </span>
          </div>

          <button
            type="button"
            onClick={() => {
              onSelectTab('dashboard');
              if (onCloseMobile) onCloseMobile();
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 mb-2 rounded-lg text-xs font-medium transition-all text-left cursor-pointer border ${
              activeTab === 'dashboard' || activeTab === 'entry' || activeTab === 'compile'
                ? 'text-cyan-300 bg-cyan-950/40 border-cyan-500/40 font-bold shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                : 'text-slate-400 bg-slate-900/40 border-slate-800/80 hover:text-cyan-200 hover:border-cyan-500/30 hover:bg-slate-800/60'
            }`}
          >
            <span className="material-symbols-outlined text-[18px] text-cyan-400">
              play_circle
            </span>
            <span className="truncate font-space-grotesk font-semibold tracking-wide">Compile Compliance</span>
          </button>

          <nav className="flex flex-col gap-1">
            {GOLDEN_PATH_NAV.map((item) => {
              const isActive = activeTab === item.id || (item.id === 'dna' && activeTab === 'input');
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    onSelectTab(item.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all text-left cursor-pointer border ${
                    isActive
                      ? 'text-cyan-300 bg-cyan-950/40 border-cyan-500/30 font-semibold shadow-[inset_0_0_10px_rgba(56,189,248,0.15)]'
                      : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <span className={`font-mono text-[10px] w-4 shrink-0 ${isActive ? 'text-cyan-400 font-bold' : 'text-slate-600'}`}>
                    {item.step}
                  </span>
                  <span
                    className={`material-symbols-outlined text-[17px] shrink-0 ${
                      isActive ? 'text-cyan-400' : 'text-slate-500'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span className="truncate">{item.title}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Divider */}
        <div className="my-2 border-t border-slate-800/80 mx-3" />

        {/* Secondary Supporting Navigation */}
        <div className="px-3 pb-3">
          <div className="px-2 pb-1.5">
            <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
              Operations & Audit
            </span>
          </div>
          <nav className="flex flex-col gap-1">
            {SECONDARY_NAV.map((item) => {
              const isCopilot = item.id === 'copilot';
              const isActive = isCopilot ? isCopilotOpen : activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    if (isCopilot) {
                      onToggleCopilot?.();
                    } else {
                      onSelectTab(item.id);
                    }
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all text-left cursor-pointer border ${
                    isActive
                      ? 'text-cyan-300 bg-cyan-950/40 border-cyan-500/40 font-semibold shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                      : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span
                      className={`material-symbols-outlined text-[17px] shrink-0 ${
                        isActive ? 'text-cyan-400' : 'text-slate-500'
                      }`}
                    >
                      {item.icon}
                    </span>
                    <span className="truncate">{item.title}</span>
                  </div>
                  {isCopilot && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0"></span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Quiet Footnote */}
      <div className="p-3.5 border-t border-slate-800/80 shrink-0 text-slate-400 text-[11px] bg-[#080c15]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono text-[10px] text-slate-300 font-semibold uppercase tracking-wider">0% LLM Compliance Authority</span>
        </div>
        <p className="mt-0.5 text-[10px] text-slate-500 font-mono">
          Deterministic Gazette Engine
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Aside */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-60 bg-[#0b0f19] border-r border-slate-800/80 z-40 flex-col shadow-xl">
        {navContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative w-64 h-full bg-[#0b0f19] z-50 shadow-2xl">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
}
