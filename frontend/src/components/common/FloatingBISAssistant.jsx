import React from 'react';

/**
 * FloatingBISAssistant
 * 
 * Persistent floating launcher widget positioned in the bottom-right corner.
 * Displays the BIS assistant icon, "BIS Assistant" label, mic indicator, and opens the conversational assistant drawer.
 */
export function FloatingBISAssistant({ onClick, isOpen }) {
  if (isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-40 font-sans">
      <button
        type="button"
        onClick={onClick}
        className="group flex items-center gap-3 px-4 py-3 bg-[#0f1422]/95 hover:bg-[#161f36] text-white rounded-full shadow-[0_8px_30px_rgba(0,0,0,0.6)] hover:shadow-[0_0_25px_rgba(56,189,248,0.35)] transition-all duration-200 cursor-pointer border border-cyan-500/30 hover:border-cyan-400 active:scale-[0.98] backdrop-blur-xl"
        aria-label="Open BIS Assistant"
        title="Open BIS Intelligent Assistant (Voice & Text supported)"
      >
        {/* Emblem Logo */}
        <div className="w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-400/40 group-hover:border-cyan-300 text-cyan-300 flex items-center justify-center shadow-[0_0_10px_rgba(56,189,248,0.3)] transition-colors">
          <span className="material-symbols-outlined text-[17px]">smart_toy</span>
        </div>

        {/* Label */}
        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5 leading-none">
            <span className="font-space-grotesk text-xs font-bold tracking-wide text-white group-hover:text-cyan-200 transition-colors">
              GOAT Copilot
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <span className="text-[10px] text-cyan-300/70 font-mono leading-none mt-1">
            Voice &amp; Statutory Guidance
          </span>
        </div>

        {/* Mic & arrow indicator */}
        <div className="flex items-center gap-1 text-cyan-400/80 group-hover:text-cyan-300 pl-1">
          <span className="material-symbols-outlined text-[16px]">mic</span>
          <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-y-0.5">
            expand_less
          </span>
        </div>
      </button>
    </div>
  );
}
