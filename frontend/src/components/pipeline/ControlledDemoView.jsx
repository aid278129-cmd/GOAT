import React, { useState } from 'react';

export function ControlledDemoView({ onLoadDemoAssessment, onNavigate }) {
  const [loadingDemoId, setLoadingDemoId] = useState(null);

  const demoCases = [
    {
      id: 'GOLDEN-SIH-2026-DEMO',
      name: 'Double-Walled Stainless Steel Vacuum Insulated Flask (750ml)',
      category: 'Drinkware & Food Contact Containers',
      standard: 'IS 17526:2021',
      qco: 'DPIIT QCO 2023 (Mandatory)',
      description: 'Double-walled vacuum insulated bottle fabricated with food-grade SS304 inner liner, SS201 outer shell, food-grade polypropylene stopper (IS 9845), rated nominal capacity 750 mL. Subjected to 6-hour thermal heat retention (measured 74.2 C vs >= 60 C limit), 10-minute inversion leakage test (passed), and laser-etched ISI rating plate.',
      clausesCount: 14,
      satisfiedCount: 14,
      status: 'SATISFIED',
      badge: 'GOLDEN SIH 2026 CASE',
      isPrimary: true,
    },
    {
      id: 'DEMO-HEATER-IS302',
      name: 'Electric Immersion Water Heater (1500W, 230V)',
      category: 'Kitchen & Domestic Appliances',
      standard: 'IS 302-2-201:2008',
      qco: 'Electrical Appliances QCO (Mandatory)',
      description: 'Portable electric immersion water heater rated at 1500W, 230V AC, 50Hz. Stainless steel 304 heating tube sheath, flame-retardant polypropylene handle, IS 694 PVC insulated flexible cord, and IS 1293 3-pin plug. Evaluated for earth continuity (< 0.1 ohm) and dielectric withstand.',
      clausesCount: 18,
      satisfiedCount: 16,
      status: 'ACTION_NEEDED',
      badge: 'ELECTRICAL APPLIANCE',
      isPrimary: false,
    },
    {
      id: 'DEMO-HELMET-IS4151',
      name: 'Protective Motorcycle Helmet (Full Face, Size L)',
      category: 'Personal Protective Equipment',
      standard: 'IS 4151:2015',
      qco: 'CMVR Statutory Mandate (Mandatory)',
      description: 'Protective helmet for two-wheeler riders with virgin ABS outer shell, expanded polystyrene (EPS) impact absorption liner, retention chin strap (22mm), and anti-scratch polycarbonate visor. Requires accredited drop impact deceleration and conical striker penetration testing.',
      clausesCount: 12,
      satisfiedCount: 10,
      status: 'ACTION_NEEDED',
      badge: 'AUTOMOTIVE / CMVR',
      isPrimary: false,
    },
  ];

  const handleSelectCase = async (demoCase) => {
    setLoadingDemoId(demoCase.id);
    try {
      // Create or seed assessment in backend
      const res = await fetch('/api/v1/assessments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: demoCase.name,
          category: demoCase.category,
          description: demoCase.description,
          authoritative_mode: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        onLoadDemoAssessment(data);
        onNavigate('dna');
      }
    } catch (err) {
      console.warn('Failed to load demo assessment:', err);
    } finally {
      setLoadingDemoId(null);
    }
  };

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
              Controlled Demonstration &bull; SIH 2026
            </span>
            <span className="text-xs text-slate-500">Problem ID: 26107 Benchmark Cases</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Evaluation & Controlled Demo Environment
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Demonstration datasets are isolated in this environment to preserve zero data contamination in normal production assessments.
          </p>
        </div>
      </div>

      {/* Isolation Policy Banner */}
      <div className="p-4 rounded-lg bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-950 space-y-1 shadow-2xs">
        <div className="flex items-center gap-2 font-bold text-indigo-900">
          <span className="material-symbols-outlined text-sm text-indigo-600">verified_user</span>
          <span>Zero Contamination Policy</span>
        </div>
        <p className="leading-relaxed text-[11px] text-indigo-900/80">
          Normal workspace workflows start completely empty. Clicking <strong>Load Into Active Compiler</strong> below copies the verified technical artifacts of the selected test case into your active session, enabling live step-by-step pipeline inspection across all 8 layers.
        </p>
      </div>

      {/* Demo Case Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {demoCases.map((c) => {
          const isLoading = loadingDemoId === c.id;

          return (
            <div
              key={c.id}
              className={`rounded-lg bg-white border p-5 shadow-2xs flex flex-col justify-between space-y-4 transition ${
                c.isPrimary ? 'border-indigo-300 ring-1 ring-indigo-200' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    c.isPrimary ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700'
                  }`}>
                    {c.badge}
                  </span>
                  <span className="text-[11px] font-mono font-bold text-slate-800">{c.standard}</span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">{c.name}</h3>
                  <span className="text-[11px] text-slate-500 font-medium block mt-0.5">{c.category}</span>
                </div>

                <div className="p-2.5 rounded bg-slate-50 border border-slate-100 text-slate-700 text-xs leading-relaxed font-mono text-[11px] line-clamp-4">
                  {c.description}
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono pt-1">
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-[10px] uppercase text-slate-400 block">Mandate</span>
                    <strong className="text-slate-800 text-[10px]">{c.qco}</strong>
                  </div>
                  <div className="p-2 rounded bg-slate-50 border border-slate-100">
                    <span className="text-[10px] uppercase text-slate-400 block">Clauses</span>
                    <strong className="text-emerald-700 text-[10px]">{c.satisfiedCount} / {c.clausesCount} Verified</strong>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleSelectCase(c)}
                disabled={isLoading}
                className={`w-full py-2 px-3 rounded text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                  c.isPrimary
                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                    : 'bg-slate-900 hover:bg-slate-800 text-white'
                }`}
              >
                <span className="material-symbols-outlined text-[15px]">
                  {isLoading ? 'hourglass_top' : 'play_arrow'}
                </span>
                <span>{isLoading ? 'Loading Dossier...' : 'Load Into Active Compiler'}</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
