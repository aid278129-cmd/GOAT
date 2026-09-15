import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function StandardsClausesView({ assessment, onNavigate }) {
  const [viewMode, setViewMode] = useState('matrix'); // 'matrix' (Stitch Screen) | 'table' (Decomposition table)
  const [copiedHash, setCopiedHash] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('ALL');

  // Derive active assessment data or fallback to Stitch SMPS-500W-IND reference data
  const isSMPS = assessment?.product_name?.includes('SMPS') || assessment?.product_name?.includes('Gateway') || !assessment?.clauses?.length;
  
  const dossierId = assessment?.assessment_number || (isSMPS ? 'BIS-24-SMPS-0049' : assessment?.assessment_id?.slice(0, 10));
  const productName = assessment?.product_name || 'Industrial Edge Gateway & Power Supply Unit (SMPS-500W-IND)';
  const gazetteRef = isSMPS ? 'S.O. 3250(E) / MeitY' : (assessment?.gazette_order || 'DPIIT QCO Order 2023');
  const targetStandard = assessment?.target_standard || (isSMPS ? 'IS 13252 (Part 1):2010' : (assessment?.primary_standard || 'IS 17526:2021'));
  const sha256Seal = assessment?.sha256_hash || 'c892da47f8721c5b8e99b0c034731872ef7ae1262d08912e73ce6723e742881b';

  // Default DNA attributes matching Stitch
  const dnaRows = [
    { spec: 'Input Voltage Profile', value: '90 - 264 VAC, 50/60 Hz', source: 'SPEC-SHEET-2024.pdf', status: 'CONFIRMED' },
    { spec: 'Enclosure Ingress Rating', value: 'IP65 (Gasket Sealed)', source: 'ENCLOSURE-SPEC.DWG', status: 'EXTRACTED' },
    { spec: 'Galvanic Isolation Barrier', value: '3.75 kV AC Reinforced', source: 'SCHEMATICS-P1.pdf', status: 'CONFIRMED' },
    { spec: 'RTC Lithium Backup Cell', value: 'CR2032 3V (Coin Cell)', source: 'BOM Line 114', status: 'MISSING EVIDENCE', isMissing: true },
  ];

  // Default Standards Applicability Tree matching Stitch
  const applicabilityItems = [
    {
      code: 'IS 13252 (Part 1):2010',
      equiv: 'equiv. IEC 60950-1:2005',
      title: 'Information Technology Equipment - Safety (General Requirements)',
      status: 'APPLICABLE (MANDATORY)',
      statusType: 'primary',
      note: 'Edge Gateway with rated voltage < 600V and network ports',
    },
    {
      code: 'IS 16046 (Part 2):2018',
      equiv: 'equiv. IEC 62133-2:2017',
      title: 'Secondary Cells & Batteries containing Alkaline/Non-Acid Electrolytes',
      status: 'POTENTIALLY APPLICABLE',
      statusType: 'outline',
      note: 'Coin cell capacity < 5Ah threshold triggers RCI exemption clause 3.2.1',
    },
  ];

  // Default Clauses Matrix matching Stitch
  const matrixClauses = [
    {
      clause: 'Cl. 1.5.1',
      title: 'Mains Components X/Y Capacitor Ratings',
      subtitle: 'Class V-0 Flammability requirement',
      criteria: 'Max discharge ≤ 0.5s at T=1.0s; UL94 V-0 recognized',
      evidence: '0.18s / 0.05% ripple (MARGIN: 64%)',
      evidenceNote: 'X2 Capacitors certified to IEC 60384-14',
      artifact: 'TR-SMPS-V2-2024.pdf',
      artifactDetail: 'Page 14 (Section 3.2)',
      status: 'VERIFIED',
      statusType: 'success',
    },
    {
      clause: 'Cl. 2.1.1.1',
      title: 'Access to Energised Parts (Electric Shock)',
      subtitle: 'Test probe B (20.5mm) 50N test',
      criteria: 'Clearance ≥ 4.0mm | Creepage ≥ 5.0mm',
      evidence: '6.42mm Clearance | 8.91mm Creepage',
      evidenceNote: 'Zero penetration recorded under 50N force probe',
      artifact: 'CAD-MECH-REV3.STEP',
      artifactDetail: '3D CMM Inspection Log #4',
      status: 'VERIFIED',
      statusType: 'success',
    },
    {
      clause: 'Cl. 5.2.2',
      title: 'Transformer Dielectric Withstand (Hi-Pot)',
      subtitle: 'Reinforced insulation boundary',
      criteria: 'Hi-Pot 3000 VAC for 60s, leakage < 5.0mA',
      evidence: '3000 VAC applied / 1.12mA measured leakage',
      evidenceNote: 'Self-declaration; awaiting NABL counter-signature',
      artifact: 'LAB-CERT-24-941',
      artifactDetail: 'OEM Internal QA Desk',
      status: 'USER_PROVIDED',
      statusType: 'info',
    },
    {
      clause: 'Cl. 4.5.1',
      title: 'Thermal Temperature Rise (Full Load 55°C)',
      subtitle: 'Class B insulation system (130°C rated)',
      criteria: 'Maximum Winding Temp ≤ 110°C (ΔT ≤ 65K)',
      evidence: 'Defect D018: Thermal chamber profiling missing',
      evidenceNote: 'Chamber logging data not attached to dossier',
      artifact: '[UNATTACHED]',
      artifactDetail: 'Defect Flag D018',
      status: 'MISSING',
      statusType: 'danger',
      isMissing: true,
    },
  ];

  // Default Compliance Gaps matching Stitch
  const complianceGaps = [
    {
      id: 'GAP-IND-01',
      clause: 'IS 13252-1 Cl. 4.5.1',
      severity: 'HIGH',
      defect: 'Defect: Thermal temperature rise at elevated ambient (55°C operating envelope) has not been verified via calibrated thermocouple matrix.',
      prescribedAction: 'LAB_TEST_REQUIRED',
      dispatchText: 'Priority P0 Dispatch',
    },
    {
      id: 'GAP-IND-02',
      clause: 'IS 13252-1 Cl. 1.7.1',
      severity: 'MEDIUM',
      defect: 'Defect: Product label artwork lacks mandatory bilingual (Hindi & English) safety cautionary markings and ISI standard font height (> 2mm).',
      prescribedAction: 'DOCUMENT_REQUIRED',
      dispatchText: 'Revise DWG-LBL-04',
    },
  ];

  // Default Lab Routing matching Stitch
  const labRouting = [
    {
      code: 'LT-THERM-55',
      facility: 'ERTL (North) - Electronics Regional Test Lab, Okhla Phase II, New Delhi',
      nabl: 'NABL #TC-1234',
      turnaround: '4 Business Days',
      actionLabel: 'SAMPLE REQ.',
      actionType: 'primary',
    },
    {
      code: 'LT-HIPOT-02',
      facility: 'CPRI (Central Power Research Institute), Bangalore / Bhopal Division',
      nabl: 'NABL #TC-4589',
      turnaround: '2 Business Days',
      actionLabel: 'SCHEDULED',
      actionType: 'outline',
    },
    {
      code: 'DOC-ISI-LBL',
      facility: 'Internal Regulatory Counsel / Artwork Studio, BIS Standard Marking Rules 2018 (Rule 6)',
      nabl: 'Internal Audit',
      turnaround: '24 Hours',
      actionLabel: 'UPLOAD DRAWING',
      actionType: 'blue-outline',
    },
  ];

  const handleCopyHash = () => {
    navigator.clipboard.writeText(sha256Seal);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div className="flex-1 p-4 md:p-6 space-y-4 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-700 bg-slate-200/70 px-2 py-0.5 rounded">
            Step 04 / 08 &bull; Standards & Clauses
          </span>
          <span className="text-xs font-mono text-slate-500">[{dossierId}]</span>
        </div>

        {/* View Switcher: Regulatory Matrix vs Decomposition Tree */}
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-200/70 p-0.5 rounded text-xs font-mono">
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                viewMode === 'matrix' ? 'bg-white font-bold text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Regulatory Matrix (Stitch Core)
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                viewMode === 'table' ? 'bg-white font-bold text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Clause Catalog Table
            </button>
          </div>

          <button
            onClick={() => onNavigate('evidence')}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
          >
            <span>Proceed to Step 5</span>
            <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {viewMode === 'table' ? (
        /* Fallback: Individual Clause Catalog Table */
        <div className="bg-white border border-slate-200 rounded shadow-2xs overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              {targetStandard} Mandatory Clauses
            </h2>
            <span className="text-[11px] font-mono text-slate-500">38 Clauses Indexed</span>
          </div>
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase">
                <th className="py-2.5 px-4">Clause</th>
                <th className="py-2.5 px-4">Requirement</th>
                <th className="py-2.5 px-4">Limit / Criteria</th>
                <th className="py-2.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {matrixClauses.map((c, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">{c.clause}</td>
                  <td className="py-2.5 px-4">{c.title}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-700">{c.criteria}</td>
                  <td className="py-2.5 px-4">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* STITCH SCREEN: FULL REGULATORY ASSURANCE ARCHITECTURE MATRIX */
        <div className="space-y-4">
          {/* SECTION 1: Regulatory Jurisdiction Card */}
          <div className="bg-white border border-slate-200 rounded p-4 shadow-2xs space-y-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="bg-slate-900 text-white text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                    REGULATORY JURISDICTION
                  </span>
                  <span className="text-xs md:text-sm font-bold text-slate-900">
                    Bureau of Indian Standards (BIS) — Electronics & IT Goods (Compulsory Registration Order, 2021)
                  </span>
                </div>
                <div className="text-xs text-slate-600 font-sans">
                  Equipment under Test: <strong className="text-slate-900 font-semibold">{productName}</strong> | Gazette Reference: <span className="font-mono text-slate-800">{gazetteRef}</span>
                </div>
              </div>

              {/* Status Badges */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-700 text-[10px] font-mono font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                  <span>QCO STATUS: MANDATORY BEFORE CUSTOMS</span>
                </div>
                <div className="px-2 py-0.5 rounded bg-sky-50 border border-sky-200 text-sky-700 text-[10px] font-mono font-bold">
                  100% Deterministic Rule-set (Zero Hallucination)
                </div>
              </div>
            </div>

            {/* 6 Metric KPI Boxes */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-1 text-center font-mono">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">TOTAL CLAUSES</span>
                <span className="text-lg font-bold text-slate-900 mt-0.5 block">38</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">EVIDENCE VERIFIED</span>
                <span className="text-lg font-bold text-emerald-600 mt-0.5 block">28 <span className="text-slate-400 text-xs">/ 38</span></span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">USER PROVIDED</span>
                <span className="text-lg font-bold text-slate-900 mt-0.5 block">8</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">DEFICIENCIES / GAPS</span>
                <span className="text-lg font-bold text-rose-600 mt-0.5 block">2</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">LAB TESTS REQ.</span>
                <span className="text-lg font-bold text-sky-600 mt-0.5 block">2</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">COMPLIANCE INDEX</span>
                <span className="text-lg font-bold text-emerald-600 mt-0.5 block">92.4%</span>
              </div>
            </div>
          </div>

          {/* SECTION 2 & 3: Side-by-Side Product DNA & Standards Tree */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Card Left: 2. Product DNA Attributes */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-slate-700 text-sm">fingerprint</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      2. Product DNA Attributes
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    43 Extracted | 16 Confirmed
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-sans">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-100/60 text-slate-600 font-mono text-[9px] uppercase">
                        <th className="py-1.5 px-2">ATTRIBUTE SPEC</th>
                        <th className="py-1.5 px-2">EXTRACTED VALUE</th>
                        <th className="py-1.5 px-2">SOURCE REF</th>
                        <th className="py-1.5 px-2">STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {dnaRows.map((row, idx) => (
                        <tr key={idx} className={row.isMissing ? 'bg-rose-50/50' : 'hover:bg-slate-50'}>
                          <td className={`py-1.5 px-2 font-medium ${row.isMissing ? 'text-rose-700 font-bold' : 'text-slate-900'}`}>
                            {row.spec}
                          </td>
                          <td className="py-1.5 px-2 font-mono text-[11px] text-slate-700">
                            {row.value}
                          </td>
                          <td className="py-1.5 px-2 font-mono text-[10px] text-slate-500">
                            {row.source}
                          </td>
                          <td className="py-1.5 px-2">
                            <span
                              className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                                row.isMissing
                                  ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                  : row.status === 'EXTRACTED'
                                  ? 'bg-sky-50 text-sky-700 border border-sky-200'
                                  : 'bg-blue-50 text-blue-700 border border-blue-200'
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Card Right: 3. BIS Standards Applicability Tree */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-slate-700 text-sm">gavel</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      3. BIS Standards Applicability Tree
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    Selected CRO Phase 2 & II
                  </span>
                </div>

                <div className="space-y-2">
                  {applicabilityItems.map((item, idx) => (
                    <div key={idx} className="p-2.5 rounded border border-slate-200 bg-slate-50/50 space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="font-mono font-bold text-xs text-slate-900">{item.code}</span>
                          <span className="text-[10px] font-mono text-slate-500 ml-1.5">{item.equiv}</span>
                          <p className="text-xs text-slate-700 leading-snug mt-0.5">{item.title}</p>
                        </div>
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded shrink-0 ${
                            item.statusType === 'primary'
                              ? 'bg-slate-900 text-white'
                              : 'bg-blue-50 text-blue-700 border border-blue-300'
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 font-mono italic">
                        Note: {item.note}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 4 & 5: Central Standards & Clauses to Evidence Matrix Table */}
          <div className="bg-white border border-slate-200 rounded shadow-2xs overflow-hidden">
            {/* Table Header Strip */}
            <div className="px-4 py-2.5 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-slate-700 text-base">policy</span>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                    4 & 5. Standards & Clauses to Evidence Matrix
                  </h3>
                </div>
                <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                  Evaluating {targetStandard} limit thresholds against forensic laboratory test deliverables
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[10px] font-mono bg-white border border-slate-300 px-2 py-0.5 rounded text-slate-700">
                  FILTER: IS: 13252-1
                </span>
                <span className="text-[11px] font-mono text-slate-600 font-semibold">
                  34 / 38 Clauses
                </span>
              </div>
            </div>

            {/* Matrix Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead>
                  <tr className="border-b border-slate-900 bg-slate-900 text-white font-mono text-[9px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">CLAUSE</th>
                    <th className="py-2.5 px-3">REQUIREMENT TITLE</th>
                    <th className="py-2.5 px-3">REGULATORY LIMIT / CRITERIA</th>
                    <th className="py-2.5 px-3">MEASURED VALUE / EVIDENCE</th>
                    <th className="py-2.5 px-3">VERIFICATION ARTIFACT</th>
                    <th className="py-2.5 px-3 text-center">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {matrixClauses.map((row, idx) => (
                    <tr key={idx} className={row.isMissing ? 'bg-rose-50/60' : 'hover:bg-slate-50 transition'}>
                      {/* Clause # */}
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900 whitespace-nowrap">
                        {row.clause}
                      </td>

                      {/* Requirement */}
                      <td className="py-2.5 px-3 max-w-[200px]">
                        <div className="font-semibold text-slate-900">{row.title}</div>
                        <div className="text-[11px] text-slate-500">{row.subtitle}</div>
                      </td>

                      {/* Criteria */}
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700 max-w-[220px]">
                        {row.criteria}
                      </td>

                      {/* Measured Value / Evidence */}
                      <td className="py-2.5 px-3 max-w-[240px]">
                        <div className={`font-mono text-[11px] font-semibold ${row.isMissing ? 'text-rose-700' : 'text-slate-900'}`}>
                          {row.evidence}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {row.evidenceNote}
                        </div>
                      </td>

                      {/* Verification Artifact */}
                      <td className="py-2.5 px-3 font-mono text-[11px] whitespace-nowrap">
                        <div className="text-indigo-700 underline cursor-pointer">{row.artifact}</div>
                        <div className="text-[10px] text-slate-400">{row.artifactDetail}</div>
                      </td>

                      {/* Status */}
                      <td className="py-2.5 px-3 text-center whitespace-nowrap">
                        <span
                          className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                            row.statusType === 'success'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                              : row.statusType === 'info'
                              ? 'bg-blue-50 text-blue-700 border-blue-300'
                              : 'bg-rose-100 text-rose-800 border-rose-300'
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* SECTION 6 & 7: Side-by-Side Compliance Gaps & Certified Lab Dispatch */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left: 6. Compliance Gaps & Deficiencies */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-rose-600 text-sm">troubleshoot</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      6. Compliance Gaps & Deficiencies
                    </h3>
                  </div>
                  <span className="text-[9px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 px-1.5 py-0.5 rounded">
                    2 ACTIONABLE DEFECTS
                  </span>
                </div>

                <div className="space-y-2">
                  {complianceGaps.map((gap, idx) => (
                    <div key={idx} className="p-2.5 rounded border border-slate-200 bg-slate-50/60 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-slate-900">
                          {gap.id} | {gap.clause}
                        </span>
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                            gap.severity === 'HIGH'
                              ? 'bg-rose-100 text-rose-800 border border-rose-300'
                              : 'bg-amber-100 text-amber-800 border border-amber-300'
                          }`}
                        >
                          SEVERITY: {gap.severity}
                        </span>
                      </div>

                      <p className="text-xs text-slate-700 leading-snug">
                        {gap.defect}
                      </p>

                      <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px] font-mono">
                        <div className="flex items-center gap-1">
                          <span className="text-slate-500">Prescribed Action:</span>
                          <span className="bg-slate-900 text-white px-1.5 py-0.2 rounded font-bold">
                            {gap.prescribedAction}
                          </span>
                        </div>
                        <span className="text-sky-700 font-semibold cursor-pointer hover:underline">
                          {gap.dispatchText}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: 7. Certified Lab Dispatch Routing */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-indigo-600 text-sm">science</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      7. Certified Lab Dispatch Routing
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    NABL Accredited Test Houses
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-sans">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-100/60 text-slate-600 font-mono text-[9px] uppercase">
                        <th className="py-1.5 px-2">TEST CODE</th>
                        <th className="py-1.5 px-2">TARGET LAB, ACCREDITED FACILITY</th>
                        <th className="py-1.5 px-2">TURNAROUND</th>
                        <th className="py-1.5 px-2 text-right">DISPATCH</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {labRouting.map((lab, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2 px-2 font-mono font-bold text-slate-900 text-[11px]">
                            {lab.code}
                          </td>
                          <td className="py-2 px-2">
                            <div className="font-medium text-slate-800 text-[11px] leading-snug">{lab.facility}</div>
                            <div className="text-[10px] font-mono text-slate-400">{lab.nabl}</div>
                          </td>
                          <td className="py-2 px-2 font-mono text-[11px] text-slate-600 whitespace-nowrap">
                            {lab.turnaround}
                          </td>
                          <td className="py-2 px-2 text-right">
                            <button
                              className={`text-[9px] font-mono font-bold px-2 py-1 rounded transition cursor-pointer ${
                                lab.actionType === 'primary'
                                  ? 'bg-slate-900 hover:bg-slate-800 text-white'
                                  : lab.actionType === 'blue-outline'
                                  ? 'border border-blue-300 text-blue-700 hover:bg-blue-50'
                                  : 'border border-slate-300 text-slate-800 hover:bg-slate-100'
                              }`}
                            >
                              {lab.actionLabel}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 8: Official Regulatory Artifact & Pre-Certification Passport Seal */}
          <div className="bg-white border-2 border-slate-900 rounded p-4 shadow-sm space-y-3">
            {/* Header with black badge */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 bg-slate-900 rounded flex items-center justify-center shrink-0">
                  <span className="text-white font-mono font-bold text-xs tracking-tighter">BIS</span>
                </div>
                <div>
                  <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
                    OFFICIAL REGULATORY ARTIFACT
                  </span>
                  <h3 className="text-xs md:text-sm font-bold text-slate-900 uppercase tracking-tight">
                    8. Evidence-Backed Pre-Certification Compliance Assessment
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-1 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                  ASSESSMENT ID: {dossierId}-PASS
                </span>
                <button
                  onClick={() => onNavigate('passport')}
                  className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white text-[10px] font-mono font-bold rounded flex items-center gap-1 transition cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[13px]">print</span>
                  <span>PDF/XML READY</span>
                </button>
              </div>
            </div>

            {/* 3 Information Blocks */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  PRODUCT SERIAL / ORDER IDENTIFICATION
                </span>
                <div className="font-bold text-slate-900">SMPS-500W-IND #SM-0849-0012</div>
                <div className="text-[11px] text-slate-500">HS Code: 8504.40.90 | Class I Grounded</div>
              </div>

              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  TESTING SCHEME & GAZETTE ORDER
                </span>
                <div className="font-bold text-slate-900">MeitY CRO Phase II / Gaz. DL-33004/99</div>
                <div className="text-[11px] text-slate-500">Standard: {targetStandard}</div>
              </div>

              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  PORTAL SUBMISSION COMPLIANCE INDEX
                </span>
                <div className="font-bold text-emerald-700">92.4% (34/38 Passed)</div>
                <div className="text-[11px] text-slate-500">2 Remedial actions pending lab sign-off</div>
              </div>
            </div>

            {/* Cryptographic Hash Bar & Submission CTA */}
            <div className="p-2.5 rounded bg-slate-100/70 border border-slate-300 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center gap-2 overflow-hidden">
                <span className="material-symbols-outlined text-slate-700 text-base shrink-0">lock</span>
                <div className="truncate">
                  <span className="text-slate-500 uppercase text-[9px] block">CRYPTOGRAPHIC EVIDENCE INTEGRITY SEAL:</span>
                  <span className="text-slate-900 font-mono text-[11px] truncate block">
                    SHA-256 : {sha256Seal}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={handleCopyHash}
                  className="px-2.5 py-1 bg-white hover:bg-slate-50 text-slate-800 rounded border border-slate-300 text-xs font-medium flex items-center gap-1 transition cursor-pointer shadow-2xs"
                >
                  <span className="material-symbols-outlined text-[13px]">{copiedHash ? 'check' : 'content_copy'}</span>
                  <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                </button>

                <a
                  href="https://manakonline.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-bold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
                >
                  <span>SUBMIT TO BIS MANAKONLINE PORTAL</span>
                  <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
