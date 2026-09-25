import React from 'react';

export const GOLDEN_PATH_NAV = [
  { id: 'assistant', step: '01', title: 'BIS AI Assistant', icon: 'smart_toy' },
  { id: 'dna', step: '02', title: 'Product DNA', icon: 'fingerprint' },
  { id: 'applicability', step: '03', title: 'BIS Applicability', icon: 'verified' },
  { id: 'standards', step: '04', title: 'Standards & Clauses', icon: 'menu_book' },
  { id: 'evidence', step: '05', title: 'Evidence Matrix', icon: 'policy' },
  { id: 'gaps', step: '06', title: 'Compliance Gaps', icon: 'rule_folder' },
  { id: 'lab', step: '07', title: 'Lab & Actions', icon: 'science' },
  { id: 'passport', step: '08', title: 'Compliance Passport', icon: 'verified_user' },
];

export const SECONDARY_NAV = [
  { id: 'workstation', title: 'Engineering Workstation', icon: 'roofing' },
  { id: 'workspace', title: 'Workspace', icon: 'developer_board' },
  { id: 'jobs', title: 'Compliance Jobs', icon: 'inventory' },
  { id: 'reviews', title: 'Review & Attestation', icon: 'rate_review' },
  { id: 'reports', title: 'Dossiers & Passports', icon: 'receipt_long' },
  { id: 'settings', title: 'Settings', icon: 'settings' },
];

// Unified list for backward compatibility & tab title lookups
export const NAV_ITEMS = [
  ...GOLDEN_PATH_NAV,
  ...SECONDARY_NAV,
];

export function SideNav({ activeTab, onSelectTab, mobileOpen, onCloseMobile }) {
  const navContent = (
    <div className="flex flex-col justify-between h-full bg-white overflow-y-auto">
      {/* Brand & Navigation */}
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="h-14 px-4 flex items-center justify-between border-b border-[#E2E8F0] shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#1D4ED8] flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-sm">shield</span>
            </div>
            <div>
              <span className="font-['Inter'] font-bold text-sm tracking-tight text-[#0F172A] block leading-none">
                ZYNTRIX
              </span>
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block mt-0.5">
                Compliance Compiler
              </span>
            </div>
          </div>
          <span className="font-mono text-[10px] text-[#64748B] bg-[#F1F5F9] px-1.5 py-0.5 rounded border border-[#E2E8F0]">
            SIH 2026
          </span>
        </div>

        {/* Primary Golden Path Section */}
        <div className="px-3 pt-3 pb-2">
          <div className="px-2 py-1 flex items-center justify-between">
            <span className="font-mono text-[10px] text-[#1D4ED8] uppercase tracking-wider font-bold">
              Compliance Compiler
            </span>
            <span className="text-[9px] font-mono bg-blue-50 text-blue-700 px-1 rounded border border-blue-200">
              Golden Path
            </span>
          </div>
          <nav className="flex flex-col gap-0.5 mt-1">
            {GOLDEN_PATH_NAV.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    onSelectTab(item.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'text-[#1D4ED8] bg-[#EFF6FF] font-semibold border-l-2 border-[#1D4ED8]'
                      : 'text-[#475569] hover:text-[#0F172A] hover:bg-[#F8F9FA]'
                  }`}
                >
                  <span className={`font-mono text-[10px] w-4 shrink-0 ${isActive ? 'text-[#1D4ED8] font-bold' : 'text-slate-500'}`}>
                    {item.step}
                  </span>
                  <span
                    className={`material-symbols-outlined text-[16px] shrink-0 ${
                      isActive ? 'text-[#1D4ED8]' : 'text-[#64748B]'
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

        {/* Secondary Stations Section */}
        <div className="px-3 pt-2 pb-2 border-t border-[#E2E8F0]">
          <div className="px-2 py-1 font-mono text-[10px] text-[#64748B] uppercase tracking-wider font-semibold">
            Secondary Stations
          </div>
          <nav className="flex flex-col gap-0.5 mt-1">
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
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'text-[#1D4ED8] bg-[#EFF6FF] font-semibold'
                      : 'text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8F9FA]'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[16px] shrink-0 ${
                      isActive ? 'text-[#1D4ED8]' : 'text-[#64748B]'
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

      {/* Sync Status & System Footnote */}
      <div className="p-3 border-t border-[#E2E8F0] shrink-0 bg-slate-50/60">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] text-[#64748B] flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            ManakOnline Sync
          </span>
          <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded border border-emerald-200">
            Authoritative
          </span>
        </div>
        <div className="mt-1 px-1 text-[10px] text-slate-500">
          Deterministic Rulebase &bull; 0% LLM Authority
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Aside */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-60 bg-white border-r border-[#E2E8F0] z-40 flex-col">
        {navContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative w-64 h-full bg-white z-50 shadow-xl">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
}
