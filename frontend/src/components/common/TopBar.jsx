import React, { useState, useRef, useEffect } from 'react';
import { MorphingInfinity } from '../loading-ui/morphing-infinity';
import GlideSelect from '../loading-ui/GlideSelect';

/**
 * TopBar (Context-Driven Dark Workstation Header)
 * 
 * Clean, compact top bar:
 * - Left: GOAT & Navigation (Home, Dashboard)
 * - Center: Contextual assessment header or clean statutory status
 * - Right: GlideSelect multilingual selector, Sources, Assistant, Help, More menu
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

  const languageOptions = [
    { value: 'en', label: 'English', tag: 'EN' },
    { value: 'hi', label: 'हिन्दी', tag: 'HI' },
    { value: 'ta', label: 'தமிழ்', tag: 'TA' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-[#0b0f19]/90 backdrop-blur-md border-b border-slate-800/80 z-30 px-4 sm:px-6 flex items-center justify-between shadow-lg font-sans">
      {/* Left: Brand or Contextual Back */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        {isAssessmentMode ? (
          <button
            type="button"
            onClick={onBackToAssistant}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-cyan-300 hover:bg-slate-800/70 border border-slate-700/60 transition-colors cursor-pointer shrink-0"
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
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-cyan-300 hover:bg-cyan-950/40 border border-slate-800 hover:border-cyan-500/30 transition-all cursor-pointer shrink-0"
          title="Return to 3D Homepage"
        >
          <span className="material-symbols-outlined text-[18px] text-cyan-400">home</span>
          <span className="hidden sm:inline">Home</span>
        </button>

        <span className="text-slate-700 select-none">|</span>

        {/* Brand identity */}
        <button
          type="button"
          onClick={() => {
            if (onSelectTab) onSelectTab('dashboard');
          }}
          className="flex items-center gap-2 text-left cursor-pointer group shrink-0"
        >
          <div className="w-6 h-6 rounded-md bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 shadow-[0_0_8px_rgba(56,189,248,0.25)] group-hover:border-cyan-300 transition-colors">
            <span className="material-symbols-outlined text-[15px]">verified</span>
          </div>
          <div>
            <span className="font-space-grotesk font-bold text-xs tracking-wider text-white uppercase block leading-tight">
              GOAT
            </span>
            {!isAssessmentMode && (
              <span className="text-[10px] text-cyan-300/60 block leading-tight font-mono hidden xs:inline">
                Statutory Compiler
              </span>
            )}
          </div>
        </button>
      </div>

      {/* Center: Contextual Assessment Header or Clean Status */}
      <div className="hidden md:flex items-center gap-2 min-w-0 px-2">
        {isAssessmentMode ? (
          <div className="flex items-center gap-2 min-w-0 bg-slate-900/80 border border-slate-800 px-3 py-1 rounded-lg">
            <span className="text-xs font-medium text-slate-200 truncate max-w-[200px] lg:max-w-[300px]" title={prodName}>
              {prodName}
            </span>
            <span className="text-slate-600">/</span>
            <span className="font-mono text-xs font-semibold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30 shrink-0">
              {standardNum}
            </span>
          </div>
        ) : (
          <span className="text-[11px] font-mono text-slate-400 bg-slate-900/60 border border-slate-800 px-3 py-1 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Bureau of Indian Standards Statutory Compliance & Services Suite</span>
          </span>
        )}
      </div>

      {/* Right: GlideSelect Multilingual, Sources, Assistant, Help, More menu */}
      <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
        {/* GlideSelect Multilingual Dropdown */}
        <div className="hidden sm:block">
          <GlideSelect
            options={languageOptions}
            value={selectedLanguage}
            onChange={(val) => onSelectLanguage && onSelectLanguage(val)}
            size="sm"
            menuWidth={135}
            surfaceColor="#0f172a"
            highlightColor="#1e293b"
            accentColor="#38bdf8"
            textColor="#f1f5f9"
            radius={8}
            ariaLabel="Select Language"
          />
        </div>

        {/* Sources Button */}
        <button
          type="button"
          onClick={onOpenSourceInspector}
          className="px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-cyan-200 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          title="Inspect statutory sources and citations"
        >
          <span className="material-symbols-outlined text-[16px] text-cyan-400">library_books</span>
          <span className="hidden sm:inline">Sources</span>
        </button>

        {/* In-Assessment AI Assistant Drawer trigger */}
        {isAssessmentMode && (
          <button
            type="button"
            onClick={onOpenAssistant}
            className="px-2.5 py-1.5 text-xs font-semibold text-cyan-300 bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-500/30 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer shadow-[0_0_10px_rgba(56,189,248,0.2)]"
            title="Open AI Engineering Assistant for this assessment"
          >
            <span className="material-symbols-outlined text-[16px]">smart_toy</span>
            <span className="hidden sm:inline">GOAT Copilot</span>
          </button>
        )}

        {/* Trust Governance & FAQ */}
        <button
          type="button"
          onClick={onOpenHelp}
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded-lg border border-transparent hover:border-slate-800 transition-colors cursor-pointer"
          title="Regulatory Governance & FAQ"
        >
          <span className="material-symbols-outlined text-[18px]">help_outline</span>
        </button>

        {/* More Tools Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded-lg border border-transparent hover:border-slate-800 transition-colors cursor-pointer"
            title="Additional tools & settings"
          >
            <span className="material-symbols-outlined text-[18px]">more_vert</span>
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-60 bg-[#0f172a] border border-slate-700/80 rounded-xl shadow-2xl py-2 z-50 text-xs backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-1 text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                Workspaces & Operations
              </div>

              {onResetDemo && (
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onResetDemo();
                  }}
                  disabled={isResettingDemo}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800/80 flex items-center gap-2 text-slate-200 cursor-pointer disabled:opacity-50 transition-colors"
                >
                  {isResettingDemo ? (
                    <MorphingInfinity className="w-4 h-4 text-cyan-400 shrink-0" />
                  ) : (
                    <span className="material-symbols-outlined text-[16px] text-cyan-400">
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
                className="w-full text-left px-3 py-2 hover:bg-slate-800/80 flex items-center gap-2 text-slate-200 cursor-pointer transition-colors"
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
                className="w-full text-left px-3 py-2 hover:bg-slate-800/80 flex items-center gap-2 text-slate-200 cursor-pointer transition-colors"
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
                className="w-full text-left px-3 py-2 hover:bg-slate-800/80 flex items-center gap-2 text-slate-200 cursor-pointer transition-colors"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">view_in_ar</span>
                <span>Engineering CAD Workstation</span>
              </button>

              <div className="my-1 border-t border-slate-800" />

              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  if (onSelectTab) onSelectTab('settings');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-800/80 flex items-center gap-2 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                <span className="material-symbols-outlined text-[16px]">settings</span>
                <span>System Configuration</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
