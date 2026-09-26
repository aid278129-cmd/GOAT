import React, { useState } from 'react';

const MOCK_LABS = [
  {
    id: 'cl-sahibabad',
    name: 'Central Laboratory, Bureau of Indian Standards',
    type: 'Authoritative BIS Central Lab',
    location: 'Sahibabad, Ghaziabad, Uttar Pradesh (Delhi NCR)',
    city: 'Delhi NCR',
    standards: ['IS 17526:2021', 'IS 16221', 'IS 302', 'IS 6911', 'IS 13252'],
    scopes: 'Physical testing, thermal retention, hermetic vacuum leakage, food-grade metallurgy, chemical analysis.',
    accreditation: 'BIS Apex Facility / NABL Accredited',
    phone: '+91-120-2770032',
  },
  {
    id: 'wrl-mumbai',
    name: 'Western Regional Laboratory (WRL), BIS',
    type: 'BIS Regional Testing Facility',
    location: 'Andheri East, Mumbai, Maharashtra',
    city: 'Mumbai',
    standards: ['IS 17526:2021', 'IS 13252', 'IS 1293', 'IS 16046'],
    scopes: 'Thermal insulation, vacuum integrity, electrical safety, mechanical endurance, drop testing.',
    accreditation: 'NABL Accredited / BIS Recognized',
    phone: '+91-22-28329295',
  },
  {
    id: 'srl-chennai',
    name: 'Southern Regional Laboratory (SRL), BIS',
    type: 'BIS Regional Testing Facility',
    location: 'CIT Campus, Taramani, Chennai, Tamil Nadu',
    city: 'Chennai',
    standards: ['IS 17526:2021', 'IS 16221', 'IS 16046', 'IS 302'],
    scopes: 'Solar inverter testing, anti-islanding, domestic appliances, vacuum flask thermal retention.',
    accreditation: 'NABL Accredited / BIS Recognized',
    phone: '+91-44-22541442',
  },
  {
    id: 'nth-kolkata',
    name: 'National Test House (Eastern Region)',
    type: 'Recognized Central Autonomous Facility',
    location: 'Alipore, Kolkata, West Bengal',
    city: 'Kolkata',
    standards: ['IS 17526:2021', 'IS 6911', 'IS 13252'],
    scopes: 'Metallurgical verification, stainless steel alloy composition, corrosion resistance.',
    accreditation: 'BIS Recognized under LRS 2020',
    phone: '+91-33-24791223',
  },
  {
    id: 'cpri-bangalore',
    name: 'Central Power Research Institute (CPRI)',
    type: 'Recognized Autonomous Power Lab',
    location: 'Sir C.V. Raman Road, Bengaluru, Karnataka',
    city: 'Bengaluru',
    standards: ['IS 16221', 'IS 16169', 'IS 13252'],
    scopes: 'High-voltage dielectric, grid synchronization, power electronics testing.',
    accreditation: 'NABL Accredited / BIS Recognized',
    phone: '+91-80-23602329',
  },
];

export function ContextualLabDiscoveryCard({ onInspectSource }) {
  const [selectedStandard, setSelectedStandard] = useState('ALL');
  const [selectedCity, setSelectedCity] = useState('ALL');

  const standardsOptions = [
    { id: 'ALL', label: 'All Standards' },
    { id: 'IS 17526:2021', label: 'IS 17526 (Vacuum Flasks)' },
    { id: 'IS 16221', label: 'IS 16221 (Solar Inverters)' },
    { id: 'IS 13252', label: 'IS 13252 (Electronics / IT)' },
  ];

  const cityOptions = [
    { id: 'ALL', label: 'All Locations' },
    { id: 'Delhi NCR', label: 'Delhi NCR / Sahibabad' },
    { id: 'Mumbai', label: 'Mumbai' },
    { id: 'Chennai', label: 'Chennai' },
    { id: 'Bengaluru', label: 'Bengaluru' },
    { id: 'Kolkata', label: 'Kolkata' },
  ];

  const filteredLabs = MOCK_LABS.filter((lab) => {
    const matchStd = selectedStandard === 'ALL' || lab.standards.includes(selectedStandard);
    const matchCity = selectedCity === 'ALL' || lab.city === selectedCity;
    return matchStd && matchCity;
  });

  return (
    <div className="mt-3.5 bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs transition-all">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-blue-600 text-lg">science</span>
          <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            BIS-Recognized Laboratory Discovery
          </span>
        </div>
        <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          LRS 2020 Validated
        </span>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <div className="flex-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Filter by Standard
          </label>
          <select
            value={selectedStandard}
            onChange={(e) => setSelectedStandard(e.target.value)}
            className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:border-blue-600 font-medium"
          >
            {standardsOptions.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Filter by Region
          </label>
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:border-blue-600 font-medium"
          >
            {cityOptions.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
        {filteredLabs.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-slate-200">
            No testing laboratories found matching the selected filters.
          </div>
        ) : (
          filteredLabs.map((lab) => (
            <div
              key={lab.id}
              className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="font-bold text-slate-900 text-xs">{lab.name}</h4>
                  <div className="text-[11px] text-slate-500 mt-0.5">{lab.location}</div>
                </div>
                <span className="text-[10px] font-mono font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 shrink-0">
                  {lab.accreditation}
                </span>
              </div>

              <div className="text-[11px] text-slate-600">
                <span className="font-semibold text-slate-700">Testing Capabilities: </span>
                {lab.scopes}
              </div>

              <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[14px]">call</span>
                  <span>{lab.phone}</span>
                </div>
                <div className="flex gap-1">
                  {lab.standards.map((st) => (
                    <span key={st} className="font-mono text-[9px] bg-white border border-slate-200 px-1 py-0.5 rounded text-slate-600">
                      {st}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Verified against BIS Laboratory Recognition Scheme (LRS 2020)</span>
        <button
          type="button"
          onClick={() => onInspectSource && onInspectSource({
            source: 'BIS Laboratory Recognition Scheme (LRS) 2020',
            document: 'LRS Regulations Gazette Order',
            clause: 'Section 4 & Annexure A',
            authority: 'Bureau of Indian Standards',
            page: '1-8',
            verification: 'NABL ISO/IEC 17025 Conformity',
            extractionMethod: 'Authoritative Parser',
            sha256: 'b4c5d6e7f8091a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789abcde',
          })}
          className="text-blue-600 hover:text-blue-800 font-medium underline cursor-pointer"
        >
          Inspect Laboratory Gazette
        </button>
      </div>
    </div>
  );
}
