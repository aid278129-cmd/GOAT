import React, { useState, useRef, useEffect } from 'react';
import { MorphingInfinity } from '../loading-ui/morphing-infinity';

/**
 * TopBar (M27.2 Assistant-First & Context-Driven)
 * 
 * Clean, compact top bar:
 * - Left: ZYNTRIX (or "← Back to Assistant" when inside an active assessment)
 * - Center: Contextual assessment header or clean search/status
 * - Right: Multilingual selector, Sources, Assistant, Help, More menu, User avatar
 */
export function TopBar({
  isAssessmentMode = false,
  onBackToAssistant,
  assessment,
  activeTab,
  onSelectTab,
  selectedLanguage = 'en',
  onSelectLanguage,
  onOpenSourceInspector,
  onOpenAssistant,
  onResetDemo,
  isResettingDemo = false,
  onOpenHelp,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const prodName = assessment?.product_name || assessment?.product_dna?.product_name || 'ThermoSteel Vacuum Flask 1000ml';
  const standardNum = assessment?.target_standard || assessment?.compliance?.standard_number || assessment?.applicability?.[0]?.standard_number || 'IS 17526:2021';

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-white border-b border-slate-200 z-30 px-4 sm:px-6 flex items-center justify-between shadow-2xs font-sans">
      {/* Left: Brand or Contextual Back */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        {isAssessmentMode ? (
          <button
            type="button"
            onClick={onBackToAssistant}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer shrink-0"
            title="Return to Compile Compliance Dashboard"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span className="hidden sm:inline">Dashboard</span>
          </button>
        ) : null}

        {/* Return to 3D Homepage button */}
        <button
          type="button"
          onClick={() => {
            if (onSelectTab) onSelectTab('home');
          }}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-cyan-600 hover:bg-cyan-50/80 transition-colors cursor-pointer shrink-0"
          title="Return to 3D Homepage (ai-based-bis-compiler)"
        >
          <span className="material-symbols-outlined text-[18px] text-cyan-600">home</span>
          <span className="hidden sm:inline">Home</span>
        </button>

        <span className="text-slate-300 select-none">|</span>

        {/* Brand identity */}
        <button
          type="button"
          onClick={() => {
            if (onSelectTab) onSelectTab('dashboard');
          }}
          className="flex items-center gap-2 text-left cursor-pointer group shrink-0"
        >
          <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white shadow-2xs group-hover:bg-blue-700 transition-colors">
            <span className="material-symbols-outlined text-[15px]">shield</span>
          </div>
          <div>
            <span className="font-bold text-xs tracking-tight text-slate-900 block leading-tight">
              ZYNTRIX
            </span>
            {!isAssessmentMode && (
              <span className="text-[10px] text-slate-500 block leading-tight hidden xs:inline">
                Statutory Compiler
              </span>
            )}
          </div>
        </button>
      </div>

      {/* Center: Contextual Assessment Header or Clean Status */}
      <div className="hidden md:flex items-center gap-2 min-w-0 px-2">
        {isAssessmentMode ? (
          <div className="flex items-center gap-2 min-w-0 bg-slate-50 border border-slate-200 px-3 py-1 rounded-lg">
            <span className="text-xs font-semibold text-slate-800 truncate max-w-[200px] lg:max-w-[300px]" title={prodName}>
              {prodName}
            </span>
            <span className="text-slate-300">/</span>
            <span className="font-mono text-xs font-semibold text-blue-700 bg-white px-2 py-0.5 rounded border border-blue-200 shrink-0">
              {standardNum}
            </span>
          </div>
        ) : (
          <span className="text-[11px] font-medium text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Bureau of Indian Standards Statutory Compliance & Services Suite</span>
          </span>
        )}
      </div>

      {/* Right: Sources, Assistant, Help, More menu, Avatar */}
      <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
        {/* Multilingual Selector */}
        <div className="hidden lg:flex items-center gap-0.5 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-[11px]">
          {[
            { id: 'en', label: 'EN' },
            { id: 'hi', label: 'हिन्दी' },
            { id: 'ta', label: 'தமிழ்' },
          ].map((lang) => (
            <button
              key={lang.id}
              type="button"
              onClick={() => onSelectLanguage && onSelectLanguage(lang.id)}
              className={`px-2 py-0.5 rounded font-medium transition-colors cursor-pointer ${
                selectedLanguage === lang.id
                  ? 'bg-white text-blue-700 font-semibold shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>

        {/* Sources Button */}
        <button
          type="button"
          onClick={onOpenSourceInspector}
          className="px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          title="Inspect statutory sources and citations"
        >
          <span className="material-symbols-outlined text-[16px] text-slate-500">library_books</span>
          <span className="hidden sm:inline">Sources</span>
        </button>

        {/* In-Assessment AI Assistant Drawer trigger */}
        {isAssessmentMode && (
          <button
            type="button"
            onClick={onOpenAssistant}
            className="px-2.5 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            title="Open AI Engineering Assistant for this assessment"
          >
            <span className="material-symbols-outlined text-[16px]">smart_toy</span>
            <span className="hidden sm:inline">Assistant</span>
          </button>
        )}

        {/* Trust Governance & FAQ */}
        <button
          type="button"
          onClick={onOpenHelp}
          className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          title="Regulatory Governance & FAQ"
        >
          <span className="material-symbols-outlined text-[18px]">help_outline</span>
        </button>

        {/* More Tools Dropdown (Collapsed Menu per M27.2 Section 10) */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            title="Additional tools & settings"
          >
            <span className="material-symbols-outlined text-[18px]">more_vert</span>
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 z-50 text-xs animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Secondary Workspaces
              </div>

              {onResetDemo && (
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onResetDemo();
                  }}
                  disabled={isResettingDemo}
                  className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 cursor-pointer disabled:opacity-50"
                >
                  {isResettingDemo ? (
                    <MorphingInfinity className="w-4 h-4 text-blue-600 shrink-0" />
                  ) : (
                    <span className="material-symbols-outlined text-[16px] text-blue-600">
                      refresh
                    </span>
                  )}
                  <span>{isResettingDemo ? 'Resetting Demo...' : 'Reset Golden Demo (IS 17526)'}</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (onSelectTab) onSelectTab('jobs');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">inventory_2</span>
                <span>Compliance Jobs Directory</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (onSelectTab) onSelectTab('reviews');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">rate_review</span>
                <span>Review & Attestation Workspace</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (onSelectTab) onSelectTab('workstation');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">view_in_ar</span>
                <span>Engineering CAD Workstation</span>
              </button>

              <div className="my-1 border-t border-slate-100" />

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (onSelectTab) onSelectTab('settings');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">settings</span>
                <span>Settings & API Configuration</span>
              </button>
            </div>
          )}
        </div>

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
