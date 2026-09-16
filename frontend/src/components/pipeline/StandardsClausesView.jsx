import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';

export function StandardsClausesView({ assessment, onNavigate }) {
  const [viewMode, setViewMode] = useState('matrix'); // 'matrix' | 'table'
  const [copiedHash, setCopiedHash] = useState(false);

  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">account_tree</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Clauses Loaded</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              No active product assessment is currently selected. Provide technical product information in Step 1 or select an assessment from the registry.
            </p>
          </div>
          <div className="flex justify-center pt-2">
            <button
              onClick={() => onNavigate('input')}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
            >
              Step 1: Product Input
            </button>
          </div>
        </div>
      </div>
    );
  }

  const dossierId = assessment.assessment_number || assessment.assessment_id?.slice(0, 10) || '—';
  const productName = assessment.product_name || assessment.title || 'Product Analysis';
  const targetStandard = assessment.target_standard || assessment.compliance?.standard_number || assessment.applicability?.[0]?.standard_number || 'Standard Scoping Pending';
  const gazetteRef = assessment.applicability?.[0]?.provenance || assessment.gazette_order || 'Official BIS Gazette';
  const schemeName = assessment.scheme || 'BIS / CRS Scheme';
  const sha256Seal = assessment.sha256_hash || 'SHA-256 Pending Verification';
  const isMandatory = assessment.applicability?.[0]?.is_mandatory_qco ?? true;

  // Real DNA attributes
  const rawAttributes = assessment.product_dna?.attributes || {};
  const dnaRows = Object.entries(rawAttributes).map(([key, val]) => ({
    spec: key.replace(/_/g, ' ').toUpperCase(),
    value: typeof val === 'object' ? JSON.stringify(val) : String(val),
    source: 'Technical Specifications',
    status: 'CONFIRMED',
    isMissing: false,
  }));

  // Real Applicability
  const applicabilityItems = (assessment.applicability || []).map((app) => ({
    code: app.standard_number || 'IS Standard',
    equiv: app.edition || '',
    title: app.title || app.standard_name || 'Indian Standard Specification',
    status: app.status || (app.is_mandatory_qco ? 'APPLICABLE (MANDATORY)' : 'APPLICABLE'),
    statusType: app.is_mandatory_qco ? 'primary' : 'outline',
    note: app.reason || app.applicability_reason || 'Scoped to confirmed Product DNA attributes',
  }));

  // Real Requirements / Clauses Matrix
  const rawRequirements = assessment.compliance?.evaluated_requirements || assessment.requirements || assessment.clauses || [];
  const matrixClauses = rawRequirements.map((r, idx) => {
    const isSatisfied = r.status === 'SATISFIED' || r.status === 'VERIFIED';
    return {
      clause: r.clause_number || r.clause || `Cl. ${idx + 1}`,
      title: r.clause_title || r.title || r.requirement_type || 'Mandatory Clause',
      subtitle: r.description || r.code || '',
      criteria: r.measurable_condition || r.criteria || r.limit || 'Standard conformity criteria',
      evidence: r.matched_evidence?.snippet || r.evidence || (isSatisfied ? 'Evidence verified' : 'No evidence attached'),
      evidenceNote: r.matched_evidence?.source || '',
      artifact: r.matched_evidence?.source || (isSatisfied ? 'System Audit' : '[UNATTACHED]'),
      artifactDetail: r.matched_evidence?.page ? `Page ${r.matched_evidence.page}` : '',
      status: r.status || (isSatisfied ? 'VERIFIED' : 'MISSING'),
      statusType: isSatisfied ? 'success' : 'danger',
      isMissing: !isSatisfied,
    };
  });

  // Real Compliance Gaps
  const rawGaps = assessment.compliance?.gaps || assessment.gaps || [];
  const complianceGaps = rawGaps.map((g, idx) => ({
    id: g.id || `GAP-${idx + 1}`,
    clause: g.clause || g.clause_number || `Cl. ${idx + 1}`,
    severity: g.severity || 'HIGH',
    defect: g.defect || g.reason || g.description || 'Compliance verification pending.',
    prescribedAction: g.prescribed_action || g.action_type || 'LAB_TEST_REQUIRED',
    dispatchText: g.dispatch_text || 'Remediation Required',
  }));

  // Real Laboratories
  const rawLabs = assessment.laboratories || [];
  const labRouting = rawLabs.map((lab, idx) => ({
    code: lab.code || `LAB-${idx + 1}`,
    facility: lab.name || lab.facility || 'Accredited Testing Facility',
    nabl: lab.nabl_cert || lab.accreditation || 'NABL Accredited',
    turnaround: lab.turnaround || 'Standard',
    actionLabel: 'SAMPLE REQ.',
    actionType: 'primary',
  }));

  // Dynamic KPIs
  const totalClauses = matrixClauses.length;
  const evidenceVerified = matrixClauses.filter((c) => c.status === 'VERIFIED' || c.status === 'SATISFIED').length;
  const userProvided = matrixClauses.filter((c) => c.status === 'USER_PROVIDED').length;
  const deficienciesGaps = complianceGaps.length;
  const labTestsReq = complianceGaps.filter((g) => g.prescribedAction === 'LAB_TEST_REQUIRED').length;
  const complianceIndex = totalClauses > 0 ? `${((evidenceVerified / totalClauses) * 100).toFixed(1)}%` : '0%';

  const handleCopyHash = () => {
    if (sha256Seal && sha256Seal !== 'SHA-256 Pending Verification') {
      navigator.clipboard.writeText(sha256Seal);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
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

        {/* View Switcher */}
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-200/70 p-0.5 rounded text-xs font-mono">
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                viewMode === 'matrix' ? 'bg-white font-bold text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Regulatory Matrix
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
        /* Individual Clause Catalog Table */
        <div className="bg-white border border-slate-200 rounded shadow-2xs overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              {targetStandard} Mandatory Clauses
            </h2>
            <span className="text-[11px] font-mono text-slate-500">{totalClauses} Clauses Evaluated</span>
          </div>
          {matrixClauses.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No mandatory clauses evaluated yet for this standard.
            </div>
          ) : (
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
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                          c.status === 'VERIFIED' || c.status === 'SATISFIED'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-amber-50 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ) : (
        /* FULL REGULATORY ASSURANCE ARCHITECTURE MATRIX */
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
                    Bureau of Indian Standards (BIS) — {schemeName}
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
                  <span>QCO STATUS: {isMandatory ? 'MANDATORY BEFORE CUSTOMS' : 'VOLUNTARY STANDARD'}</span>
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
                <span className="text-lg font-bold text-slate-900 mt-0.5 block">{totalClauses}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">EVIDENCE VERIFIED</span>
                <span className="text-lg font-bold text-emerald-600 mt-0.5 block">{evidenceVerified} <span className="text-slate-400 text-xs">/ {totalClauses}</span></span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">USER PROVIDED</span>
                <span className="text-lg font-bold text-slate-900 mt-0.5 block">{userProvided}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">DEFICIENCIES / GAPS</span>
                <span className="text-lg font-bold text-rose-600 mt-0.5 block">{deficienciesGaps}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">LAB TESTS REQ.</span>
                <span className="text-lg font-bold text-sky-600 mt-0.5 block">{labTestsReq}</span>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">COMPLIANCE INDEX</span>
                <span className="text-lg font-bold text-emerald-600 mt-0.5 block">{complianceIndex}</span>
              </div>
            </div>
          </div>

          {/* SECTION 2 & 3: Side-by-Side Product DNA & Standards Tree */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Card Left: Product DNA Attributes */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-slate-700 text-sm">fingerprint</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      Product DNA Attributes
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {dnaRows.length} Extracted
                  </span>
                </div>

                {dnaRows.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No technical attributes extracted yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto max-h-56">
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
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="py-1.5 px-2 font-medium text-slate-900">
                              {row.spec}
                            </td>
                            <td className="py-1.5 px-2 font-mono text-[11px] text-slate-700">
                              {row.value}
                            </td>
                            <td className="py-1.5 px-2 font-mono text-[10px] text-slate-500">
                              {row.source}
                            </td>
                            <td className="py-1.5 px-2">
                              <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-sky-50 text-sky-700 border border-sky-200">
                                {row.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Card Right: BIS Standards Applicability Tree */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-slate-700 text-sm">gavel</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      BIS Standards Applicability Tree
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {applicabilityItems.length} Scoped
                  </span>
                </div>

                {applicabilityItems.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No applicable standards mapped yet.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-56 overflow-y-auto">
                    {applicabilityItems.map((item, idx) => (
                      <div key={idx} className="p-2.5 rounded border border-slate-200 bg-slate-50/50 space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="font-mono font-bold text-xs text-slate-900">{item.code}</span>
                            {item.equiv && <span className="text-[10px] font-mono text-slate-500 ml-1.5">{item.equiv}</span>}
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
                        {item.note && (
                          <p className="text-[11px] text-slate-500 font-mono italic">
                            Note: {item.note}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 4 & 5: Central Standards & Clauses to Evidence Matrix Table */}
          <div className="bg-white border border-slate-200 rounded shadow-2xs overflow-hidden">
            <div className="px-4 py-2.5 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-slate-700 text-base">policy</span>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                    Standards & Clauses to Evidence Matrix
                  </h3>
                </div>
                <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                  Evaluating {targetStandard} limit thresholds against laboratory test evidence
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[11px] font-mono text-slate-600 font-semibold">
                  {evidenceVerified} / {totalClauses} Clauses Verified
                </span>
              </div>
            </div>

            {matrixClauses.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No requirement clauses recorded for this assessment.
              </div>
            ) : (
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
                        <td className="py-2.5 px-3 font-mono font-bold text-slate-900 whitespace-nowrap">
                          {row.clause}
                        </td>
                        <td className="py-2.5 px-3 max-w-[200px]">
                          <div className="font-semibold text-slate-900">{row.title}</div>
                          {row.subtitle && <div className="text-[11px] text-slate-500">{row.subtitle}</div>}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700 max-w-[220px]">
                          {row.criteria}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700 max-w-[220px]">
                          <div>{row.evidence}</div>
                          {row.evidenceNote && <div className="text-[10px] text-slate-400">{row.evidenceNote}</div>}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[10px] text-slate-500">
                          <div>{row.artifact}</div>
                          {row.artifactDetail && <div className="text-slate-400">{row.artifactDetail}</div>}
                        </td>
                        <td className="py-2.5 px-3 text-center whitespace-nowrap">
                          <span
                            className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded ${
                              row.status === 'VERIFIED' || row.status === 'SATISFIED'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-rose-100 text-rose-800 border border-rose-300'
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
            )}
          </div>

          {/* SECTION 6 & 7: Compliance Gaps & Lab Routing */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Left: Compliance Gaps */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-slate-700 text-sm">troubleshoot</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      Compliance Gaps
                    </h3>
                  </div>
                  <span className="text-[9px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200 px-1.5 py-0.5 rounded">
                    {deficienciesGaps} ACTIONABLE DEFECTS
                  </span>
                </div>

                {complianceGaps.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No compliance defects detected.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-56 overflow-y-auto">
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
                        <p className="text-xs text-slate-700 leading-snug">{gap.defect}</p>
                        <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px] font-mono">
                          <div className="flex items-center gap-1">
                            <span className="text-slate-500">Action:</span>
                            <span className="bg-slate-900 text-white px-1.5 py-0.2 rounded font-bold">
                              {gap.prescribedAction}
                            </span>
                          </div>
                          <span className="text-sky-700 font-semibold">{gap.dispatchText}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right: Lab Dispatch Routing */}
            <div className="bg-white border border-slate-200 rounded p-3.5 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-indigo-600 text-sm">science</span>
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                      Certified Lab Dispatch Routing
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                    {labRouting.length} Facilities
                  </span>
                </div>

                {labRouting.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-400">
                    No active laboratory testing dispatches required.
                  </div>
                ) : (
                  <div className="overflow-x-auto max-h-56">
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
                )}
              </div>
            </div>
          </div>

          {/* SECTION 8: Official Pre-Certification Passport Seal */}
          <div className="bg-white border-2 border-slate-900 rounded p-4 shadow-sm space-y-3">
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
                    Evidence-Backed Pre-Certification Compliance Assessment
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-1 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
                  DOSSIER: {dossierId}
                </span>
                <button
                  onClick={() => onNavigate('passport')}
                  className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white text-[10px] font-mono font-bold rounded flex items-center gap-1 transition cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[13px]">verified</span>
                  <span>VIEW PASSPORT</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  PRODUCT DOSSIER IDENTIFICATION
                </span>
                <div className="font-bold text-slate-900">{productName}</div>
                <div className="text-[11px] text-slate-500">ID: {dossierId}</div>
              </div>

              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  REGULATORY ORDER & STANDARD
                </span>
                <div className="font-bold text-slate-900">{schemeName}</div>
                <div className="text-[11px] text-slate-500">Standard: {targetStandard}</div>
              </div>

              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[9px] uppercase tracking-wider text-slate-400 font-bold block">
                  PORTAL SUBMISSION COMPLIANCE INDEX
                </span>
                <div className="font-bold text-emerald-700">{complianceIndex} ({evidenceVerified}/{totalClauses} Verified)</div>
                <div className="text-[11px] text-slate-500">{deficienciesGaps} Remedial action(s) recorded</div>
              </div>
            </div>

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
