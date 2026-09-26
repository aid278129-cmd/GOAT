import React from 'react';

/**
 * FloatingBISAssistant
 * 
 * Persistent floating launcher widget positioned in the bottom-right corner.
 * Displays the BIS emblem icon, "BIS Assistant" label, and opens the conversational assistant drawer.
 */
export function FloatingBISAssistant({ onClick, isOpen }) {
  if (isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-40 font-sans">
      <button
        type="button"
        onClick={onClick}
        className="group flex items-center gap-2.5 px-4 py-3 bg-slate-900 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer border border-slate-700 hover:border-blue-500 active:scale-[0.98]"
        aria-label="Open BIS Assistant"
        title="Open BIS Intelligent Assistant (Indian Standards, Schemes, Labs, Hallmarking)"
      >
        {/* BIS Emblem Logo */}
        <div className="w-6 h-6 rounded-full bg-blue-600 group-hover:bg-white text-white group-hover:text-blue-700 flex items-center justify-center shadow-xs transition-colors">
          <span className="material-symbols-outlined text-[16px]">shield</span>
        </div>

        {/* Label */}
        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5 leading-none">
            <span className="text-xs font-bold tracking-tight">BIS Assistant</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          </div>
          <span className="text-[10px] text-slate-300 group-hover:text-blue-100 font-medium leading-none mt-1">
            Indian Standards & Schemes
          </span>
        </div>

        {/* Arrow / Quick expand indicator */}
        <span className="material-symbols-outlined text-sm text-slate-400 group-hover:text-white transition-transform group-hover:translate-x-0.5">
          arrow_upward
        </span>
      </button>
    </div>
  );
}
