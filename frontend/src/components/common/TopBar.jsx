import React from 'react';

export function TopBar({
  currentView,
  onNavigate,
  onNewAnalysis,
  mobileMenuOpen,
  setMobileMenuOpen,
  productName,
  isHealthy = true,
  healthDetails,
  onClearAll,
}) {
  const navItems = [
    { id: 'templates', label: 'Generate Template' },
    { id: 'overview', label: 'Overview' },
    { id: 'analyze', label: 'Product Input' },
    { id: 'workspace', label: 'Product DNA' },
    { id: 'standards', label: 'Standards & Gaps' },
    { id: 'assistant', label: 'Copilot' },
    { id: 'passport', label: 'Passport' },
    { id: 'knowledge', label: 'BIS Catalog' },
    { id: 'evaluation', label: 'Evaluation Console' },
    { id: 'diagnostics', label: 'Architecture & Health' },
  ];

  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-4 md:px-6 shrink-0 sticky top-0 z-30 shadow-2xs">
      {/* Left: Mobile Menu Toggle & Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden text-slate-500 p-1.5 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer"
          aria-label="Toggle navigation menu"
        >
          <span className="material-symbols-outlined">{mobileMenuOpen ? 'close' : 'menu'}</span>
        </button>

        <div className="flex lg:hidden items-center gap-2">
          <div className="w-7 h-7 bg-indigo-600 rounded flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-xs">ZY</span>
          </div>
          <span className="font-bold text-sm text-slate-900">Zyntrix</span>
        </div>

        {/* Active Product Name Indicator */}
        {productName ? (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-full">
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-medium text-indigo-700">
              Active: <strong className="font-semibold text-indigo-900">{productName}</strong>
            </span>
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-100 border border-slate-200 rounded-full">
            <span className="text-xs text-slate-500">
              No product selected &mdash; Enter details to start
            </span>
          </div>
        )}
      </div>

      {/* Right: Mode, Backend Status, and Actions */}
      <div className="flex items-center gap-2.5">
        {/* Authoritative Mode Indicator */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 border border-blue-200 rounded-lg text-[11px] font-semibold text-blue-700">
          <span className="material-symbols-outlined text-[15px] text-blue-600">verified</span>
          <span>Authoritative Mode</span>
        </div>

        {/* Backend Online / Healthy Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-[11px] font-semibold text-emerald-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="hidden sm:inline">Backend:</span>
          <span>{isHealthy ? 'ONLINE' : 'DEGRADED'}</span>
        </div>

        {/* Clear All Button */}
        {onClearAll && (
          <button
            onClick={onClearAll}
            className="hidden md:flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-red-700 hover:bg-red-50 border border-slate-200 hover:border-red-200 transition"
            title="Clear all assessments and start fresh"
          >
            <span className="material-symbols-outlined text-[15px]">refresh</span>
            <span>Reset</span>
          </button>
        )}

        {/* New Assessment Primary Button */}
        <button
          onClick={onNewAnalysis}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all shadow-xs cursor-pointer active:scale-95"
        >
          <span className="material-symbols-outlined text-[15px]">add</span>
          <span>New Product</span>
        </button>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-x-0 top-16 bg-white border-b border-slate-200 p-4 shadow-xl z-50 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                onNavigate(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold ${
                currentView === item.id
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
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
