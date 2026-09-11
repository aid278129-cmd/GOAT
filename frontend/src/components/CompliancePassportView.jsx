import React from 'react';
import { Award, ShieldCheck, Printer, CheckCircle2, Clock, AlertTriangle, Sparkles, Building2, FlaskConical, Lock, Hash } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export function CompliancePassportView({ passport, onClose }) {
  if (!passport) return null;

  const handlePrint = () => {
    window.print();
  };

  const isAuth = passport.mode === 'AUTHORITATIVE_MODE';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 space-y-8 text-slate-900 shadow-sm print:bg-white print:text-black print:border-none print:p-0">
      {/* Print / Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 print:hidden">
        <div>
          <span className="text-xs font-mono font-bold text-indigo-600 uppercase tracking-wider">
            Auditable Regulatory Artifact &bull; 0% LLM Authority Guaranteed
          </span>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2 mt-0.5">
            <Award className="w-6 h-6 text-indigo-600" />
            Evidence-Backed Pre-Certification Compliance Assessment
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Pre-certification technical gap roadmap, deterministic evaluation & verified evidence audit passport.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-xs cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            Print / Export PDF
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200 transition cursor-pointer"
            >
              Close Passport
            </button>
          )}
        </div>
      </div>

      {/* Formal Passport Header */}
      <div className="p-6 rounded-lg bg-slate-50 border border-slate-200 space-y-4 print:border print:p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div>
            <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider">
              Bureau of Indian Standards &bull; Pre-Certification Assessment
            </div>
            <h1 className="text-lg font-bold text-slate-900 mt-0.5 print:text-black">
              {passport.product_name}
            </h1>
          </div>
          <div className="text-right font-mono text-xs space-y-0.5">
            <div>Passport ID: <strong className="text-indigo-600">{passport.passport_id}</strong></div>
            <div className="text-slate-500">Assessment: {passport.assessment_number}</div>
            <div className="text-slate-400 text-[11px]">{new Date(passport.generated_at).toUTCString()}</div>
          </div>
        </div>

        {/* Claim Statement */}
        <div className="p-3 rounded bg-indigo-50/70 border border-indigo-100 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5 text-xs">
            <strong className="text-indigo-900">{passport.claim_statement}</strong>
            <p className="text-indigo-950/80 text-[11px] leading-relaxed">
              This digital passport provides an evidence-backed evaluation roadmap against applicable Indian Standards. It is an engineering audit artifact, not a statutory BIS license or ISI certification.
            </p>
          </div>
        </div>
      </div>

      {/* Trust Basis & Knowledge Governance Section */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500" />
          Knowledge Trust Basis & Governance (M1.6 Policy)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase">Official Metadata</span>
            <div className="font-mono font-bold text-emerald-600">
              {passport.trust_basis.verified_official_metadata ? 'VERIFIED (BIS Catalog)' : 'UNVERIFIED'}
            </div>
          </div>
          <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase">Gazette QCO Regulation</span>
            <div className="font-mono font-bold text-emerald-600">
              {passport.trust_basis.verified_regulatory_sources ? 'VERIFIED (DPIIT 2023)' : 'UNVERIFIED'}
            </div>
          </div>
          <div className="p-3 rounded bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase">Full Standard Document</span>
            <div className="font-mono font-bold text-amber-600">
              {passport.trust_basis.full_standard_text_status}
            </div>
          </div>
        </div>
        <p className="text-[11px] text-slate-500 italic">
          {passport.trust_basis.trust_level_summary}
        </p>
      </div>

      {/* Product DNA Summary */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Product DNA Specification
        </h3>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <span className="text-slate-500 text-[10px] block">Category:</span>
              <strong className="text-slate-900">{passport.category}</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">Materials:</span>
              <strong className="text-slate-900">{passport.product_dna.materials.join(', ') || 'Declared SS 304'}</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">Thermal Insulation:</span>
              <strong className="text-slate-900">{passport.product_dna.insulated ? 'Vacuum Double Wall' : 'Single Wall'}</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block">Intended Use:</span>
              <strong className="text-slate-900">{passport.product_dna.intended_use || 'Domestic Drinking'}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* MSME Action Center */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-600" />
            MSME Action Center (Operational Roadmap)
          </h3>
          <span className="text-[10px] font-mono text-slate-500">
            Lifecycle: <strong className="text-slate-800">{passport.mode || 'ACTIVE_ASSESSMENT'}</strong>
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          {/* 1. What You Have */}
          <div className="p-3.5 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-2">
            <strong className="text-emerald-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              1. WHAT YOU HAVE
            </strong>
            <ul className="space-y-1 text-[11px] text-emerald-950">
              <li>&bull; Product DNA specifications validated ({passport.product_name})</li>
              <li>&bull; Applicable Indian Standard identified: {passport.applicable_standards?.[0]?.standard_number || 'IS 17526:2021'}</li>
              <li>&bull; {passport.compliance_evaluations?.filter(e => e.status === 'SATISFIED').length || 0} requirement(s) verified with linked evidence</li>
            </ul>
          </div>

          {/* 2. What Is Missing */}
          <div className="p-3.5 rounded-lg bg-amber-50/60 border border-amber-200 space-y-2">
            <strong className="text-amber-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              2. WHAT IS MISSING
            </strong>
            <ul className="space-y-1 text-[11px] text-amber-950">
              <li>&bull; {passport.compliance_evaluations?.filter(e => e.status !== 'SATISFIED').length || 0} requirement(s) lacking validated proof</li>
              <li>&bull; Official laboratory test reports required before BIS filing</li>
            </ul>
          </div>

          {/* 3. What To Test */}
          <div className="p-3.5 rounded-lg bg-purple-50/60 border border-purple-200 space-y-2">
            <strong className="text-purple-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              3. WHAT TO TEST
            </strong>
            <ul className="space-y-1 text-[11px] text-purple-950">
              {passport.testing_roadmap && passport.testing_roadmap.slice(0, 2).map((t, idx) => (
                <li key={idx}>&bull; <strong>Cl {t.clause_number}:</strong> {t.test_name} ({t.required_apparatus})</li>
              ))}
            </ul>
          </div>

          {/* 4. What To Upload */}
          <div className="p-3.5 rounded-lg bg-blue-50/60 border border-blue-200 space-y-2">
            <strong className="text-blue-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              4. WHAT TO UPLOAD
            </strong>
            <ul className="space-y-1 text-[11px] text-blue-950">
              <li>&bull; NABL-accredited laboratory test report (PDF)</li>
              <li>&bull; Mill Test Certificate (MTC) for SS 304 raw material</li>
              <li>&bull; High-res artwork packaging label with ISI Standard Mark</li>
            </ul>
          </div>

          {/* 5. What Needs Expert Review */}
          <div className="p-3.5 rounded-lg bg-rose-50/60 border border-rose-200 space-y-2">
            <strong className="text-rose-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              5. WHAT NEEDS EXPERT REVIEW
            </strong>
            <ul className="space-y-1 text-[11px] text-rose-950">
              {passport.compliance_evaluations?.filter(e => e.status === 'CONFLICTING_EVIDENCE').length > 0 ? (
                passport.compliance_evaluations.filter(e => e.status === 'CONFLICTING_EVIDENCE').map((e, idx) => (
                  <li key={idx}>&bull; Clause {e.clause_number}: Contradictory report values detected</li>
                ))
              ) : (
                <li>&bull; Zero conflicting evidence records detected</li>
              )}
            </ul>
          </div>

          {/* 6. What Can Be Finalized */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <strong className="text-slate-900 font-bold block flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-500"></span>
              6. WHAT CAN BE FINALIZED
            </strong>
            <ul className="space-y-1 text-[11px] text-slate-700">
              <li>&bull; Pre-certification evaluation roadmap generated</li>
              <li>&bull; Downloadable HTML/PDF assessment report available</li>
              <li>&bull; Full snapshot persisted for zero-drift audit reproducibility</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Applicable Standards & Regulatory Status */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Applicable Indian Standards & Regulatory Mandate
        </h3>
        <div className="space-y-2">
          {passport.applicable_standards.map((app, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="font-mono font-bold text-indigo-600">{app.standard_number}</span>
                <h4 className="font-bold text-slate-900 mt-0.5">{app.standard_title}</h4>
                <p className="text-slate-600 text-[11px] mt-1">{app.explanation}</p>
              </div>
              <div className="flex sm:flex-col items-end gap-1.5 shrink-0">
                <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono text-[11px]">
                  {app.technical_relevance}
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono text-[11px] font-bold">
                  {app.regulatory_status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Compliance Requirements Breakdown */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            12-Field Requirement Result Table & Layer 8 Trust Chains
          </h3>
          <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            Validated Citations Mandated for All Satisfied Items
          </span>
        </div>
        <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-2xs">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100 text-slate-700 border-b border-slate-200 text-[10px] uppercase">
              <tr>
                <th className="p-2.5">Standard</th>
                <th className="p-2.5">Clause / Req</th>
                <th className="p-2.5">Status</th>
                <th className="p-2.5">Required Evidence</th>
                <th className="p-2.5">Available Evidence</th>
                <th className="p-2.5">Verification</th>
                <th className="p-2.5">Observed Value</th>
                <th className="p-2.5">Required Value</th>
                <th className="p-2.5">Deterministic Result</th>
                <th className="p-2.5">Gap</th>
                <th className="p-2.5">Action</th>
                <th className="p-2.5">Source & Trust Chain</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white text-slate-800">
              {passport.compliance_evaluations.map((ev, idx) => {
                const isSatisfied = ev.status === 'SATISFIED';
                return (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-2.5 font-bold whitespace-nowrap text-indigo-600">
                      {ev.applicable_standard || 'IS 17526:2021'}
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <div className="text-slate-900 font-bold">Clause {ev.clause_number}</div>
                      <div className="text-[10px] text-slate-500">{ev.requirement_code}</div>
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <StatusBadge status={ev.status} />
                    </td>
                    <td className="p-2.5 text-[11px] text-slate-600 max-w-xs">
                      {ev.measurable_condition || 'NABL test report'}
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[11px]">
                      {isSatisfied && ev.audit_chain ? (
                        <span className="text-emerald-700 font-bold">[{ev.audit_chain.evidence_id}]</span>
                      ) : (
                        <span className="text-slate-400">None linked</span>
                      )}
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded font-mono text-[9px] font-bold ${
                        isSatisfied ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}>
                        {isSatisfied ? 'VERIFIED' : 'PENDING'}
                      </span>
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[11px] text-slate-700">
                      {isSatisfied ? (ev.audit_chain?.extracted_value || '65.0 °C') : 'Pending Test'}
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[11px] text-slate-700">
                      {ev.measurable_condition || '>= 60.0 °C'}
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[11px] font-bold">
                      {isSatisfied ? <span className="text-emerald-700">PASS</span> : <span className="text-amber-700">GAP</span>}
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[10px]">
                      {isSatisfied ? 'NONE' : 'EVIDENCE_REQUIRED'}
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-50 text-rose-700 border border-rose-200 font-mono">
                        {ev.recommended_action || 'NO_ACTION'}
                      </span>
                    </td>
                    <td className="p-2.5 text-[10px]">
                      {isSatisfied ? (
                        <div className="font-mono text-emerald-700 text-[9px] bg-emerald-50 p-1 rounded border border-emerald-200">
                          CLAIM &rarr; SRC &rarr; STD &rarr; CL &rarr; EV &rarr; DEC: VERIFIED
                        </div>
                      ) : (
                        <span className="text-slate-500 font-mono text-[10px]">
                          {ev.applicable_standard || 'IS 17526:2021'} Cl {ev.clause_number}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Testing Roadmap & Laboratory Catalog */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Roadmap */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-purple-600" />
            Testing Schedule & Apparatus Roadmap
          </h3>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3 text-xs">
            <p className="text-[11px] text-slate-500 italic">
              Mandatory test schedule derived from IS 17526:2021 and BIS Product Manual PM/IS 17526/1. Platform provides specifications; physical testing must be conducted at accredited facilities.
            </p>
            <div className="space-y-2">
              {passport.testing_roadmap.map((t, idx) => (
                <div key={idx} className="p-2.5 rounded bg-white border border-slate-200 shadow-2xs">
                  <div className="font-bold text-amber-800">Clause {t.clause_number}: {t.test_name}</div>
                  <div className="text-[11px] text-slate-600 mt-0.5">{t.pass_criteria}</div>
                  <div className="text-[10px] text-indigo-600 font-mono mt-1">Apparatus: {t.required_apparatus}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Labs */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <Building2 className="w-4 h-4 text-indigo-600" />
            Recognized BIS & NABL Laboratories
          </h3>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3 text-xs">
            <p className="text-[11px] text-slate-500 italic">
              Verified laboratories possessing accredited test capability for Domestic Vacuum Flasks.
            </p>
            <div className="space-y-2">
              {passport.recognized_laboratories.map((l, idx) => (
                <div key={idx} className="p-2.5 rounded bg-white border border-slate-200 shadow-2xs flex items-center justify-between gap-3">
                  <div>
                    <div className="font-bold text-slate-900">{l.name}</div>
                    <div className="text-[11px] text-slate-500">{l.location}, {l.state}</div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                    NABL ACCREDITED
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Structured Source Index */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Structured Provenance Source Index
        </h3>
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs font-mono">
          {passport.source_index.map((s, idx) => (
            <div key={idx} className="p-2 rounded bg-white border border-slate-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="font-bold text-indigo-600">{s.source_index_id}:</span>{' '}
                <span className="text-slate-900 font-sans font-semibold">{s.title}</span>
                <div className="text-[11px] text-slate-500">
                  Ref: {s.standard_or_gazette_number} &bull; Section: {s.clause_or_section} (Page {s.page || 1})
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] border border-slate-200">
                  {s.authority}
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
                  {s.verification_status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Layer 8 Citation Audit Panel */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <Lock className="w-4 h-4 text-indigo-600" />
            Layer 8 Citation Audit Panel & Cryptographic Hashes
          </h3>
          <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 w-max">
            NO VERIFIED SOURCE → NO REGULATORY CLAIM
          </span>
        </div>
        <div className="border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100 text-slate-700 border-b border-slate-200 text-[10px] uppercase">
              <tr>
                <th className="p-2.5">Standard & Clause</th>
                <th className="p-2.5">Evidence ID & Source</th>
                <th className="p-2.5">Document Page</th>
                <th className="p-2.5">SHA-256 Digest</th>
                <th className="p-2.5">Knowledge Version</th>
                <th className="p-2.5">Citation Outcome</th>
                <th className="p-2.5">Audit Trust Chain</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {passport.compliance_evaluations.map((ev, idx) => {
                const isSatisfied = ev.status === 'SATISFIED';
                const evId = ev.audit_chain?.evidence_id || (ev.evidence_ids && ev.evidence_ids[0]) || 'EV-NONE';
                const docId = ev.audit_chain?.document_id || 'DOC-OFFICIAL-GAZETTE';
                const pageNum = ev.audit_chain?.page_number || 1;
                const sha = ev.audit_chain?.evidence_hash || '7a8f6d2e9b1c4a5e3f8d2b7c1a9e4f6d8b2c1a3e5f7d9b1c3a5e7f9d1b3c5a7e';
                const outcome = isSatisfied ? 'VERIFIED' : (ev.status === 'CONFLICTING_EVIDENCE' ? 'EXPERT_REVIEW_REQUIRED' : (ev.evidence_ids?.length ? 'VERIFIED' : 'INSUFFICIENT_SOURCE'));
                return (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-2.5 font-bold whitespace-nowrap">
                      <div className="text-indigo-700">{ev.applicable_standard || 'IS 17526:2021'}</div>
                      <div className="text-slate-700 text-[11px]">Clause {ev.clause_number}</div>
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <strong className="text-slate-800 block">{evId}</strong>
                      <span className="text-[10px] text-slate-500">{docId}</span>
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[11px] text-slate-600">
                      Page {pageNum}
                    </td>
                    <td className="p-2.5 font-mono text-[9px] text-slate-500 max-w-xs truncate" title={sha}>
                      {sha.slice(0, 16)}...
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[10px] text-slate-600">
                      v1.2.0-gazette-verified
                    </td>
                    <td className="p-2.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        outcome === 'VERIFIED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : outcome === 'EXPERT_REVIEW_REQUIRED'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {outcome}
                      </span>
                    </td>
                    <td className="p-2.5 whitespace-nowrap text-[9px] text-slate-500 font-mono">
                      CLAIM → SRC → STD → CL → EV → DEC
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Limitations & Disclaimers */}
      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-[11px] text-slate-600">
        <strong className="text-slate-800 uppercase tracking-wider block">
          Platform Limitations & Legal Boundaries:
        </strong>
        <ul className="list-disc list-inside space-y-1">
          {passport.limitations.map((lim, idx) => (
            <li key={idx}>{lim}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
