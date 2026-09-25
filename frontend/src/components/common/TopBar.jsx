import React, { useState } from 'react';

/**
 * TopBar
 * 
 * Compact, clean workstation top bar for M27.1.
 * Left: ZYNTRIX Compliance Compiler (or assessment breadcrumbs inside workflow)
 * Center/right: Current assessment & Current standard
 * Right: Assistant, Help, User
 * 
 * Dynamically adapts to entry screen vs. active workflow.
 */
export function TopBar({
  activeTabTitle,
  onToggleMobile,
  assessment,
  isEntryScreen = false,
  onOpenAssistant,
  onOpenSourceInspector,
  onResetDemo,
  isResettingDemo = false,
  onOpenHelp,
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const prodName = assessment?.product_name || assessment?.product_dna?.product_name || 'ThermoSteel Vacuum Flask 1000ml';
  const standardNum = assessment?.target_standard || assessment?.compliance?.standard_number || assessment?.applicability?.[0]?.standard_number || 'IS 17526:2021';

  return (
    <header className={`fixed top-0 left-0 ${!isEntryScreen ? 'lg:left-60' : ''} right-0 h-14 bg-white border-b border-slate-200 z-30 px-4 sm:px-6 flex items-center justify-between shadow-2xs`}>
      {/* Left: Mobile Toggle & Workstation Brand Context */}
      <div className="flex items-center gap-3 sm:gap-5 min-w-0">
        {!isEntryScreen && (
          <button
            type="button"
            onClick={onToggleMobile}
            className="lg:hidden p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            <span className="material-symbols-outlined text-xl">menu</span>
          </button>
        )}

        {/* Brand Identity on Entry or Mobile */}
        {(isEntryScreen || !assessment) ? (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center text-white shadow-xs">
              <span className="material-symbols-outlined text-sm">shield</span>
            </div>
            <span className="font-bold text-xs tracking-tight text-slate-900">ZYNTRIX</span>
            <span className="text-[11px] text-slate-500 hidden sm:inline">&bull; Compliance Compiler</span>
          </div>
        ) : (
          /* Current Assessment & Target Standard Breadcrumb inside workflow */
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider hidden sm:inline">
                Assessment:
              </span>
              <span className="text-xs font-semibold text-slate-900 truncate max-w-[180px] md:max-w-[240px]" title={prodName}>
                {prodName}
              </span>
            </div>

            <span className="text-slate-300">/</span>

            <div className="flex items-center gap-1.5 min-w-0">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider hidden sm:inline">
                Standard:
              </span>
              <span className="text-xs font-mono font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {standardNum}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Right: Actions, Search, AI Assistant, Help, User */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Search (only inside workflow) */}
        {!isEntryScreen && (
          <div className="relative hidden md:flex items-center">
            <span className="material-symbols-outlined text-[16px] text-slate-400 absolute left-2.5 pointer-events-none">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-48 lg:w-56 pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
              placeholder="Search clauses or evidence..."
            />
          </div>
        )}

        {/* AI Assistant Quick Trigger */}
        <button
          type="button"
          onClick={onOpenAssistant}
          className="px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:text-blue-700 hover:bg-blue-50/70 border border-slate-200 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          title="Open AI Assistant"
        >
          <span className="material-symbols-outlined text-[16px] text-blue-600">smart_toy</span>
          <span className="hidden sm:inline">Assistant</span>
        </button>

        {/* Reset Demo (only inside workflow) */}
        {!isEntryScreen && onResetDemo && (
          <button
            type="button"
            onClick={onResetDemo}
            disabled={isResettingDemo}
            className="px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-50"
            title="Reset Golden SIH Demo Assessment"
          >
            <span className={`material-symbols-outlined text-[15px] ${isResettingDemo ? 'animate-spin' : ''}`}>
              refresh
            </span>
            <span className="hidden md:inline">{isResettingDemo ? 'Resetting...' : 'Reset'}</span>
          </button>
        )}

        {/* Help / Trust FAQ */}
        <button
          type="button"
          onClick={onOpenHelp}
          className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          title="Regulatory Governance & FAQ"
        >
          <span className="material-symbols-outlined text-[18px]">help_outline</span>
        </button>

        {/* User profile avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-semibold">
            LE
          </div>
        </div>
      </div>
    </header>
  );
}
