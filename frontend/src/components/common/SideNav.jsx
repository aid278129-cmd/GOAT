import React from 'react';

export const NAV_ITEMS = [
  { id: 'workstation', title: 'Home / Workstation', icon: 'roofing' },
  { id: 'workspace', title: 'Workspace', icon: 'developer_board' },
  { id: 'jobs', title: 'Compliance Jobs', icon: 'rule_folder' },
  { id: 'evidence', title: 'Evidence Ingestion', icon: 'policy' },
  { id: 'dna', title: 'Product DNA', icon: 'fingerprint' },
  { id: 'standards', title: 'Standards & Clauses', icon: 'menu_book' },
  { id: 'reviews', title: 'Review & Attestation', icon: 'rate_review' },
  { id: 'reports', title: 'Dossiers & Passports', icon: 'verified_user' },
  { id: 'settings', title: 'Settings', icon: 'settings' },
];

export function SideNav({ activeTab, onSelectTab, mobileOpen, onCloseMobile }) {
  const primaryNav = NAV_ITEMS.slice(0, 8);
  const settingsNav = NAV_ITEMS.slice(8);

  const navContent = (
    <div className="flex flex-col justify-between h-full bg-white">
      {/* Brand & Navigation */}
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="h-14 px-4 flex items-center justify-between border-b border-[#E2E8F0]">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#1D4ED8] flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined text-sm">shield</span>
            </div>
            <span className="font-['Inter'] font-bold text-sm tracking-tight text-[#0F172A]">
              ZYNTRIX
            </span>
          </div>
          <span className="font-mono text-[11px] text-[#64748B] bg-[#F1F5F9] px-1.5 py-0.5 rounded border border-[#E2E8F0]">
            BIS v4.2
          </span>
        </div>

        {/* Pipeline Nav List */}
        <div className="px-3 py-3">
          <div className="px-2 py-1 font-mono text-[10px] text-[#64748B] uppercase tracking-wider font-semibold">
            Statutory Pipeline
          </div>
          <nav className="flex flex-col gap-0.5 mt-1">
            {primaryNav.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    onSelectTab(item.id);
                    if (onCloseMobile) onCloseMobile();
                  }}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded text-xs font-medium transition-colors text-left ${
                    isActive
                      ? 'text-[#1D4ED8] bg-[#EFF6FF] font-semibold'
                      : 'text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8F9FA]'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-base ${
                      isActive ? 'text-[#1D4ED8]' : 'text-[#64748B]'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span>{item.title}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Settings & System Health Footnote */}
      <div className="p-3 border-t border-[#E2E8F0]">
        <nav className="flex flex-col gap-0.5">
          {settingsNav.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  onSelectTab(item.id);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded text-xs font-medium transition-colors text-left ${
                  isActive
                    ? 'text-[#1D4ED8] bg-[#EFF6FF] font-semibold'
                    : 'text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8F9FA]'
                }`}
              >
                <span
                  className={`material-symbols-outlined text-base ${
                    isActive ? 'text-[#1D4ED8]' : 'text-[#64748B]'
                  }`}
                >
                  {item.icon}
                </span>
                <span>{item.title}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-2 pt-2 border-t border-[#E2E8F0] flex items-center justify-between px-1">
          <span className="text-[11px] text-[#64748B] flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            ManakOnline Sync
          </span>
          <span className="font-mono text-[10px] text-[#94A3B8]">Ready</span>
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
