import React, { useState } from 'react';

export function TopBar({ activeTabTitle, onToggleMobile }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 lg:left-60 right-0 h-14 bg-white border-b border-[#E2E8F0] z-30 px-4 sm:px-6 flex items-center justify-between">
      {/* Left: Mobile Toggle & Context Breadcrumb */}
      <div className="flex items-center gap-3 sm:gap-4 flex-1 min-w-0">
        <button
          type="button"
          onClick={onToggleMobile}
          className="lg:hidden p-1.5 text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8F9FA] rounded"
        >
          <span className="material-symbols-outlined text-xl">menu</span>
        </button>

        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
          <span className="font-mono text-xs text-[#0F172A] font-medium truncate">
            BIS Gazette: Synchronized
          </span>
          <span className="hidden sm:inline-block font-mono text-[10px] text-[#64748B] bg-[#F8F9FA] px-1.5 py-0.5 rounded border border-[#E2E8F0]">
            IS Gazette 2026.09
          </span>
        </div>

        <div className="hidden xl:flex items-center gap-2 pl-3 border-l border-[#E2E8F0]">
          <span className="text-xs text-[#64748B]">Context:</span>
          <span className="font-mono text-xs text-[#0F172A] font-semibold">
            {activeTabTitle || 'Production Workstation'}
          </span>
        </div>
      </div>

      {/* Right: Search, Notifications, Profile */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Universal Search Input */}
        <div className="relative hidden md:flex items-center">
          <span className="material-symbols-outlined text-sm text-[#94A3B8] absolute left-2.5 pointer-events-none">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-56 lg:w-72 pl-8 pr-12 py-1 text-xs bg-[#F8F9FA] border border-[#E2E8F0] rounded text-[#0F172A] placeholder-[#94A3B8] focus:outline-none focus:border-[#1D4ED8] focus:bg-white transition-all"
            placeholder="Search standards, jobs, clauses, or evidence..."
          />
          <span className="absolute right-2 font-mono text-[10px] text-[#94A3B8] border border-[#E2E8F0] px-1 rounded bg-white pointer-events-none">
            Ctrl+K
          </span>
        </div>

        <div className="hidden md:block h-4 w-px bg-[#E2E8F0]" />

        {/* Notifications Popover */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-1.5 text-[#64748B] hover:text-[#0F172A] hover:bg-[#F8F9FA] rounded transition-colors"
            title="Notifications"
          >
            <span className="material-symbols-outlined text-lg">notifications</span>
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-[#E2E8F0] rounded-lg shadow-xl p-4 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="flex items-center justify-between pb-2 border-b border-[#E2E8F0] mb-3">
                <span className="font-semibold text-xs text-[#0F172A]">Statutory Notifications</span>
                <span className="font-mono text-[10px] text-[#94A3B8]">0 Unread</span>
              </div>
              <div className="py-6 text-center text-[#64748B]">
                <span className="material-symbols-outlined text-2xl text-slate-300 mb-1 block">
                  notifications_paused
                </span>
                <p className="text-xs font-medium text-[#0F172A]">No unread notifications</p>
                <p className="text-[11px] text-[#94A3B8] mt-0.5">
                  Audit events and gazette amendments will appear here.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Engineer Profile Avatar */}
        <div className="flex items-center gap-2 pl-1 border-l border-[#E2E8F0]">
          <div className="w-7 h-7 rounded-full bg-[#1D4ED8] text-white flex items-center justify-center font-bold text-xs shadow-sm">
            RE
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs text-[#0F172A] font-medium leading-none">
              Regulatory Engineer
            </span>
            <span className="font-mono text-[10px] text-[#64748B] leading-tight mt-0.5">
              Unassigned Org
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
