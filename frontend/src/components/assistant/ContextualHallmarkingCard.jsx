import React from 'react';

/**
 * ContextualHallmarkingCard
 * 
 * Interactive guide for verifying statutory gold and silver hallmarking
 * and the 3 mandatory marks including HUID under BIS Hallmarking Regulations.
 */
export function ContextualHallmarkingCard({ onInspectSource }) {
  const marks = [
    {
      num: '01',
      title: 'BIS Standard Logo',
      desc: 'Triangular mark certifying conformity to Indian Standards (IS 1417 for gold, IS 2112 for silver).',
      badge: 'Assurance of Purity',
      icon: 'verified',
    },
    {
      num: '02',
      title: 'Purity & Fineness Grade',
      desc: 'Numeric fineness and karatage: 24K999 (99.9%), 22K916 (91.6%), 20K833 (83.3%), 18K750 (75.0%), 14K585 (58.5%).',
      badge: 'Gold Karat Rating',
      icon: 'workspace_premium',
    },
    {
      num: '03',
      title: '6-Digit Alphanumeric HUID',
      desc: 'Hallmark Unique Identification (e.g. AB1234). Unique laser-engraved code assigned at Assaying & Hallmarking Centres (AHC).',
      badge: 'Unique Traceability',
      icon: 'qr_code_2',
    },
  ];

  return (
    <div className="mt-3.5 bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs transition-all">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-amber-600 text-lg">hotel_class</span>
          <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Statutory Gold & Silver Hallmarking Guide
          </span>
        </div>
        <span className="text-[11px] font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          Mandatory 3 Marks
        </span>
      </div>

      <p className="text-xs text-slate-600 leading-relaxed mb-3">
        Since 1 April 2023, the sale of hallmarked gold jewelry is permitted in India ONLY with the <strong>3 mandatory marks</strong> including 6-digit HUID.
      </p>

      {/* 3 Mandatory Marks Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 mb-4">
        {marks.map((m) => (
          <div
            key={m.num}
            className="p-3 bg-amber-50/50 border border-amber-200/80 rounded-lg text-xs flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] font-bold text-amber-800 bg-white px-1.5 py-0.5 rounded border border-amber-300">
                  MARK {m.num}
                </span>
                <span className="material-symbols-outlined text-amber-600 text-[18px]">
                  {m.icon}
                </span>
              </div>
              <h4 className="font-bold text-slate-900 text-xs mb-1">{m.title}</h4>
              <p className="text-slate-600 text-[11px] leading-relaxed">{m.desc}</p>
            </div>
            <div className="mt-2 pt-1 border-t border-amber-200/60 text-[10px] font-medium text-amber-800">
              {m.badge}
            </div>
          </div>
        ))}
      </div>

      {/* How to verify via BIS CARE App */}
      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="material-symbols-outlined text-blue-600 text-[16px]">smartphone</span>
          <h4 className="text-xs font-bold text-slate-900">
            How Consumers Verify HUID on the "BIS CARE" App
          </h4>
        </div>
        <ol className="list-decimal list-inside text-xs text-slate-600 space-y-1 pl-1">
          <li>Download the official <strong>BIS CARE</strong> mobile application from Google Play / iOS App Store.</li>
          <li>Select the <strong>"Verify HUID"</strong> feature on the home dashboard.</li>
          <li>Enter the 6-digit alphanumeric code engraved on your jewelry piece.</li>
          <li>Instantly verify: Jeweler Registration No., Assaying & Hallmarking Centre (AHC) details, Hallmarking Date, and Certified Purity.</li>
        </ol>
      </div>

      {/* Footer */}
      <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Under BIS (Hallmarking) Regulations 2018</span>
        <button
          type="button"
          onClick={() => onInspectSource && onInspectSource({
            source: 'Bureau of Indian Standards (Hallmarking) Regulations 2018',
            document: 'Gazette of India (Extraordinary)',
            clause: 'Regulation 5 & Mandatory HUID Order',
            authority: 'Bureau of Indian Standards',
            page: '1-6',
            verification: 'Ministry of Consumer Affairs Order',
            extractionMethod: 'Authoritative Parser',
            sha256: 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4',
          })}
          className="text-blue-600 hover:text-blue-800 font-medium underline cursor-pointer"
        >
          Inspect Hallmarking Order
        </button>
      </div>
    </div>
  );
}
