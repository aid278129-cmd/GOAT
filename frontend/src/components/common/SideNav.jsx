import React from 'react';

/**
 * SideNav
 * 
 * Compact vertical workstation navigation for M27.1.
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
  { id: 'dna', step: '01', title: 'Product', icon: 'fingerprint' },
  { id: 'applicability', step: '02', title: 'Applicability', icon: 'verified' },
  { id: 'standards', step: '03', title: 'Requirements', icon: 'rule' },
  { id: 'evidence', step: '04', title: 'Evidence', icon: 'policy' },
  { id: 'gaps', step: '05', title: 'Gaps', icon: 'rule_folder' },
  { id: 'lab', step: '06', title: 'Actions', icon: 'science' },
  { id: 'passport', step: '07', title: 'Assessment', icon: 'verified_user' },
];

export const SECONDARY_NAV = [
  { id: 'assistant', title: 'Assistant', icon: 'smart_toy' },
  { id: 'jobs', title: 'Jobs', icon: 'inventory_2' },
  { id: 'workspace', title: 'Workspace', icon: 'dashboard' },
  { id: 'reviews', title: 'Review', icon: 'rate_review' },
  { id: 'workstation', title: 'Knowledge Base', icon: 'auto_stories' },
  { id: 'settings', title: 'Settings', icon: 'settings' },
];

export const NAV_ITEMS = [
  ...GOLDEN_PATH_NAV,
  ...SECONDARY_NAV,
];

export function SideNav({ activeTab, onSelectTab, mobileOpen, onCloseMobile }) {
  const navContent = (
    <div className="flex flex-col justify-between h-full bg-white font-sans overflow-y-auto">
      {/* Brand & Navigation */}
      <div className="flex flex-col">
        {/* Top Brand Block */}
        <div className="h-14 px-5 flex items-center justify-between border-b border-slate-200 shrink-0">
          <button 
            type="button"
            onClick={() => onSelectTab('entry')}
            className="flex items-center gap-2.5 text-left cursor-pointer group"
          >
            <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white shadow-2xs group-hover:bg-blue-700 transition-colors">
              <span className="material-symbols-outlined text-[15px]">shield</span>
            </div>
            <div>
              <span className="font-bold text-xs tracking-tight text-slate-900 block leading-tight">
                ZYNTRIX
              </span>
              <span className="text-[10px] text-slate-500 block leading-tight">
                Compliance Compiler
              </span>
            </div>
          </button>
        </div>

        {/* Primary Compiler Workflow */}
        <div className="px-3 pt-4 pb-2">
          <div className="px-2 pb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Compliance Compiler
            </span>
          </div>
          <nav className="flex flex-col gap-0.5">
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
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all text-left cursor-pointer ${
                    isActive
                      ? 'text-blue-700 bg-blue-50/80 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <span className={`font-mono text-[11px] w-4 shrink-0 ${isActive ? 'text-blue-700 font-bold' : 'text-slate-400'}`}>
                    {item.step}
                  </span>
                  <span
                    className={`material-symbols-outlined text-[17px] shrink-0 ${
                      isActive ? 'text-blue-700' : 'text-slate-400'
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
        <div className="my-2 border-t border-slate-100 mx-3" />

        {/* Secondary Supporting Navigation */}
        <div className="px-3 pb-3">
          <div className="px-2 pb-1.5">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Secondary
            </span>
          </div>
          <nav className="flex flex-col gap-0.5">
            {SECONDARY_NAV.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    onSelectTab(item.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all text-left cursor-pointer ${
                    isActive
                      ? 'text-blue-700 bg-blue-50/80 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[17px] shrink-0 ${
                      isActive ? 'text-blue-700' : 'text-slate-400'
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
      </div>

      {/* Quiet Footnote */}
      <div className="p-4 border-t border-slate-100 shrink-0 text-slate-400 text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span className="font-medium text-slate-600">Deterministic Rulebase</span>
        </div>
        <p className="mt-0.5 text-[10px] text-slate-400">
          Zyntrix Workstation v2.0
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Aside */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-60 bg-white border-r border-slate-200 z-40 flex-col">
        {navContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
            onClick={onCloseMobile}
          />
          <div className="relative w-64 h-full bg-white z-50 shadow-2xl">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
}
