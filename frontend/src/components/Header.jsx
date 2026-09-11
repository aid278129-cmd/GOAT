import React from 'react';
import { ShieldCheck, Database, Layers, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

export function Header({ health, isRefreshing, onRefresh }) {
  const getStatusPill = () => {
    if (!health) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          Checking Connection...
        </span>
      );
    }
    if (health.status === 'ok') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Backend Live & Operational
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
        <span className="w-2 h-2 rounded-full bg-rose-500"></span>
        API Active (Database Degraded)
      </span>
    );
  };

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-50 px-6 py-4 shadow-2xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-600">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900">BIS Compliance Compiler</h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                Team Zyntrix
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Bureau of Indian Standards &bull; Smart Automation &bull; Evidence-Backed Compliance Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end md:self-auto">
          {getStatusPill()}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition disabled:opacity-50 cursor-pointer"
            title="Refresh System Health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
    </header>
  );
}
