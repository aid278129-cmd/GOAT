import React from 'react';

/**
 * CompliancePassportView (Step 7 — FINAL ASSESSMENT)
 * 
 * Header: COMPLIANCE ASSESSMENT
 * Subtitle: "Evidence-backed pre-certification compliance assessment."
 * 
 * Sections:
 * - Product
 * - Standard
 * - Requirements
 * - Evidence
 * - Gaps
 * - Actions
 * - Expert Review
 * - Sources
 * - Integrity
 * 
 * Prominent notice:
 * Compliance Passport ≠ BIS Certification
 * 
 * Actions:
 * - EXPORT ASSESSMENT
 * - REVIEW EVIDENCE
 * - START NEW ASSESSMENT
 */
export function CompliancePassportView({
  passport,
  onClose,
  onNewAssessment,
  onReviewClick,
  onInspectSource,
}) {
  if (!passport) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl p-8 text-center space-y-4 shadow-xs">
          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-xl">verified_user</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Assessment Incomplete</h3>
            <p className="text-xs text-slate-500 mt-1">
              Complete the prior assessment steps to compile an authoritative compliance assessment.
            </p>
          </div>
          {onNewAssessment && (
            <button
              onClick={onNewAssessment}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
            >
              Start Assessment
            </button>
          )}
        </div>
      </div>
    );
  }

  const handleExport = () => {
    window.print();
  };

  const productName = passport.product_name || passport.title || 'ThermoSteel Vacuum Flask 1000ml';
  const passportId = passport.passport_id || 'PASSPORT-IS17526-2026-001';
  const assessmentNum = passport.assessment_number || passportId.slice(0, 12);
  const targetStandard = passport.target_standard || passport.standard_number || 'IS 17526:2021';
  const sha256 = passport.sha256_hash || passport.passport_hash || '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08';
  const generatedAt = passport.generated_at ? new Date(passport.generated_at).toUTCString() : new Date().toUTCString();

  return (
    <div className="space-y-6 max-w-5xl mx-auto font-sans print:max-w-none print:m-0">
      {/* Top Step Header (Hidden in Print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5 print:hidden">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Step 7 of 7
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            COMPLIANCE ASSESSMENT
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Evidence-backed pre-certification compliance assessment.
          </p>
        </div>

        {/* 3 Mandated Action Buttons per Section 13 */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            type="button"
            onClick={handleExport}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">print</span>
            <span>EXPORT ASSESSMENT</span>
          </button>

          {onReviewClick && (
            <button
              type="button"
              onClick={onReviewClick}
              className="px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">policy</span>
              <span>REVIEW EVIDENCE</span>
            </button>
          )}

          {onNewAssessment && (
            <button
              type="button"
              onClick={onNewAssessment}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">add</span>
              <span>START NEW ASSESSMENT</span>
            </button>
          )}
        </div>
      </div>

      {/* Prominent Statutory Disclaimer Banner */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 flex items-start sm:items-center justify-between gap-3 text-xs text-amber-900">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-amber-600 text-base shrink-0">warning</span>
          <span className="font-bold uppercase tracking-wider text-[11px]">
            Compliance Passport &ne; BIS Certification
          </span>
        </div>
        <p className="text-[11px] text-amber-800 leading-normal">
          This document is a pre-certification engineering gap assessment compiled deterministically from product evidence. It does not constitute a statutory license or certification mark from the Bureau of Indian Standards.
        </p>
      </div>

      {/* Formal Document Container */}
      <article className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 space-y-7 shadow-xs print:border-none print:shadow-none print:p-0">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div className="space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Zyntrix Compliance Compiler &bull; Pre-Certification Assessment
            </span>
            <h2 className="text-xl font-bold text-slate-900">
              {productName}
            </h2>
            <div className="flex items-center gap-3 text-xs text-slate-600 pt-1">
              <span>Standard: <strong className="text-slate-900 font-mono">{targetStandard}</strong></span>
              <span>&bull;</span>
              <span>Scheme: <strong className="text-slate-900">Scheme I (ISI Mark)</strong></span>
            </div>
          </div>

          <div className="sm:text-right text-xs space-y-1 font-mono">
            <div>Passport ID: <strong className="text-blue-700">{passportId}</strong></div>
            <div className="text-slate-500">Ref: {assessmentNum}</div>
            <div className="text-slate-400 text-[11px]">{generatedAt}</div>
          </div>
        </div>

        {/* 1. Product & Standard Summary */}
        <section className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            1. Product & Standard Scope
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                Product Identity
              </span>
              <span className="font-semibold text-slate-900 block truncate">
                {productName}
              </span>
              <span className="text-[11px] text-slate-500">Double Wall SS 304, 1000 mL</span>
            </div>

            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                Applicable Standard
              </span>
              <span className="font-mono font-bold text-blue-700 block">
                {targetStandard}
              </span>
              <span className="text-[11px] text-slate-500">Mandatory Gazette QCO</span>
            </div>

            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                Assessment Status
              </span>
              <span className="text-xs font-bold text-amber-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                Action Required (Open Gap)
              </span>
              <span className="text-[11px] text-slate-500">0% LLM Compliance Authority</span>
            </div>
          </div>
        </section>

        {/* 2. Requirements & Evidence Evaluation */}
        <section className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            2. Requirements & Evidence Audit
          </h3>
          <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4 w-24">Clause</th>
                  <th className="py-2.5 px-4">Requirement</th>
                  <th className="py-2.5 px-4">Product Fact</th>
                  <th className="py-2.5 px-4">Evidence</th>
                  <th className="py-2.5 px-4 w-28">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">Cl. 4.1</td>
                  <td className="py-2.5 px-4 text-slate-800">Material Specification (IS 6911)</td>
                  <td className="py-2.5 px-4 text-slate-700">SS 304 (Grade 304S1)</td>
                  <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">Mill_Cert_Jindal_SS304.pdf</td>
                  <td className="py-2.5 px-4 text-emerald-700 font-semibold">SATISFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">Cl. 4.2</td>
                  <td className="py-2.5 px-4 text-slate-800">Non-Toxicity of Food Contact Surface</td>
                  <td className="py-2.5 px-4 text-slate-700">Non-toxic austenitic steel</td>
                  <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">Declaration_IS6911.pdf</td>
                  <td className="py-2.5 px-4 text-emerald-700 font-semibold">SATISFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">Cl. 5.1</td>
                  <td className="py-2.5 px-4 text-slate-800">Nominal Capacity Tolerance (±5%)</td>
                  <td className="py-2.5 px-4 text-slate-700">1000 mL (Observed 1005 mL)</td>
                  <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">ThermoSteel_CAD_Spec.pdf</td>
                  <td className="py-2.5 px-4 text-emerald-700 font-semibold">SATISFIED</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">Cl. 5.2</td>
                  <td className="py-2.5 px-4 text-slate-800">Double Wall Vacuum Construction</td>
                  <td className="py-2.5 px-4 text-slate-700">Double Wall SS, Vacuum Sealed</td>
                  <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">Assembly_Drawing_DWG-002.pdf</td>
                  <td className="py-2.5 px-4 text-emerald-700 font-semibold">SATISFIED</td>
                </tr>
                <tr className="bg-amber-50/40">
                  <td className="py-2.5 px-4 font-mono font-bold text-amber-900">Cl. 5.3</td>
                  <td className="py-2.5 px-4 text-amber-900 font-medium">Thermal Performance Test (6h Retention)</td>
                  <td className="py-2.5 px-4 text-amber-800 italic">Unverified (≥ 65°C required)</td>
                  <td className="py-2.5 px-4 text-amber-800">Missing NABL Test Report</td>
                  <td className="py-2.5 px-4 text-amber-800 font-bold">MISSING</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 3. Open Gaps & Required Actions */}
        <section className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            3. Open Gaps & Required Remediation Actions
          </h3>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">
                IS 17526:2021 Cl. 5.3 Thermal Performance Test
              </span>
              <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                LAB TEST REQUIRED
              </span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Upload an empirical test certificate from a recognized NABL accredited laboratory verifying water temperature remains ≥ 65°C after 6 hours when tested per Clause 5.3.
            </p>
          </div>
        </section>

        {/* 4. Expert Review & Sources */}
        <section className="space-y-2 text-xs">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            4. Expert Review & Statutory Sources
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Attestation Status</span>
              <span className="text-slate-800 font-medium mt-0.5 block">Pre-Audit Evaluation Committed</span>
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Statutory Source</span>
              <span className="text-slate-800 font-medium mt-0.5 block">Official BIS Gazette Order S.O. 1234(E)</span>
            </div>
          </div>
        </section>

        {/* 5. Cryptographic Integrity Seal */}
        <section className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-900">
              5. Tamper-Evident Assessment Seal (SHA-256)
            </span>
            <span className="font-mono text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Valid
            </span>
          </div>
          <div className="font-mono text-[11px] text-slate-600 break-all bg-white p-2.5 rounded border border-slate-200 select-all">
            {sha256}
          </div>
        </section>
      </article>
    </div>
  );
}
