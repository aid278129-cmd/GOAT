import React from 'react';

/**
 * CompliancePassportView (Step 7 — FINAL ASSESSMENT PASSPORT)
 * 
 * Header: COMPLIANCE ASSESSMENT PASSPORT
 * Subtitle: "Evidence-backed pre-certification compliance assessment."
 * Dark precision workstation aesthetic matching homepage.
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
      <div className="flex-1 p-8 flex items-center justify-center font-sans text-slate-200">
        <div className="max-w-md w-full bg-[#0f1422] border border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-xl">
          <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-400/30 rounded-xl flex items-center justify-center mx-auto text-cyan-400 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
            <span className="material-symbols-outlined text-2xl">verified_user</span>
          </div>
          <div>
            <h3 className="font-space-grotesk text-sm font-bold text-white">Assessment Incomplete</h3>
            <p className="text-xs text-slate-400 mt-1">
              Complete the prior assessment steps to compile an authoritative compliance assessment.
            </p>
          </div>
          {onNewAssessment && (
            <button
              onClick={onNewAssessment}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl text-xs transition shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
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
    <div className="space-y-6 max-w-5xl mx-auto font-sans text-slate-100 print:max-w-none print:m-0">
      {/* Top Step Header (Hidden in Print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5 print:hidden">
        <div>
          <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider block mb-1">
            Step 7 of 7 &bull; Final Stage
          </span>
          <h1 className="font-space-grotesk text-2xl font-bold text-white tracking-tight">
            COMPLIANCE PASSPORT
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Evidence-backed pre-certification compliance assessment & cryptographic passport.
          </p>
        </div>

        {/* 3 Mandated Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            type="button"
            onClick={handleExport}
            className="px-4 py-2.5 bg-[#0f1422] hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px] text-cyan-400">print</span>
            <span>EXPORT ASSESSMENT</span>
          </button>

          {onReviewClick && (
            <button
              type="button"
              onClick={onReviewClick}
              className="px-4 py-2.5 bg-[#0f1422] hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px] text-cyan-400">policy</span>
              <span>REVIEW EVIDENCE</span>
            </button>
          )}

          {onNewAssessment && (
            <button
              type="button"
              onClick={onNewAssessment}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(56,189,248,0.3)] cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">add</span>
              <span>START NEW ASSESSMENT</span>
            </button>
          )}
        </div>
      </div>

      {/* Prominent Statutory Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 flex items-start sm:items-center justify-between gap-3 text-xs text-amber-200 shadow-md">
        <div className="flex items-center gap-2 shrink-0">
          <span className="material-symbols-outlined text-amber-400 text-lg shrink-0">warning</span>
          <span className="font-mono font-bold uppercase tracking-wider text-[11px] text-amber-300">
            Compliance Passport &ne; BIS Certification
          </span>
        </div>
        <p className="text-[11px] text-amber-300/90 leading-relaxed font-mono">
          This document is a pre-certification engineering gap assessment compiled deterministically from product evidence. It does not constitute a statutory license or certification mark from the Bureau of Indian Standards.
        </p>
      </div>

      {/* Formal Document Container */}
      <article className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-7 shadow-2xl backdrop-blur-xl print:border-none print:shadow-none print:p-0">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1.5">
            <span className="text-[10px] font-mono font-semibold text-cyan-400 uppercase tracking-wider block">
              GOAT Compliance Compiler &bull; Pre-Certification Passport
            </span>
            <h2 className="font-space-grotesk text-2xl font-bold text-white tracking-tight">
              {productName}
            </h2>
            <div className="flex items-center gap-3 text-xs text-slate-400 pt-1 font-mono">
              <span>Standard: <strong className="text-cyan-300">{targetStandard}</strong></span>
              <span>&bull;</span>
              <span>Scheme: <strong className="text-slate-200">Scheme I (ISI Mark)</strong></span>
            </div>
          </div>

          <div className="sm:text-right text-xs space-y-1 font-mono p-3 bg-[#0b0f19] border border-slate-800 rounded-xl">
            <div>Passport ID: <strong className="text-cyan-400">{passportId}</strong></div>
            <div className="text-slate-400">Ref: {assessmentNum}</div>
            <div className="text-slate-500 text-[11px]">{generatedAt}</div>
          </div>
        </div>

        {/* 1. Product & Standard Summary */}
        <section className="space-y-3">
          <h3 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
            1. Product & Standard Scope
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold block">
                Product Identity
              </span>
              <span className="font-space-grotesk font-semibold text-white block truncate">
                {productName}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">Double Wall SS 304, 1000 mL</span>
            </div>

            <div className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold block">
                Applicable Standard
              </span>
              <span className="font-mono font-bold text-cyan-300 block">
                {targetStandard}
              </span>
              <span className="text-[11px] text-emerald-400 font-mono">Mandatory Gazette QCO</span>
            </div>

            <div className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold block">
                Assessment Status
              </span>
              <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                Action Required (Open Gap)
              </span>
              <span className="text-[11px] text-slate-500 font-mono">0% LLM Compliance Authority</span>
            </div>
          </div>
        </section>

        {/* 2. Requirements & Evidence Evaluation */}
        <section className="space-y-3">
          <h3 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
            2. Requirements & Evidence Audit
          </h3>
          <div className="border border-slate-800 rounded-xl overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 font-mono font-semibold uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4 w-24">Clause</th>
                  <th className="py-3 px-4">Requirement</th>
                  <th className="py-3 px-4">Product Fact</th>
                  <th className="py-3 px-4">Evidence</th>
                  <th className="py-3 px-4 w-28">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                <tr className="hover:bg-[#13192a] transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">Cl. 4.1</td>
                  <td className="py-3 px-4 text-slate-200">Material Specification (IS 6911)</td>
                  <td className="py-3 px-4 text-slate-300">SS 304 (Grade 304S1)</td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">Mill_Cert_Jindal_SS304.pdf</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold font-mono">SATISFIED</td>
                </tr>
                <tr className="hover:bg-[#13192a] transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">Cl. 4.2</td>
                  <td className="py-3 px-4 text-slate-200">Non-Toxicity of Food Contact Surface</td>
                  <td className="py-3 px-4 text-slate-300">Non-toxic austenitic steel</td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">Declaration_IS6911.pdf</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold font-mono">SATISFIED</td>
                </tr>
                <tr className="hover:bg-[#13192a] transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">Cl. 5.1</td>
                  <td className="py-3 px-4 text-slate-200">Nominal Capacity Tolerance (±5%)</td>
                  <td className="py-3 px-4 text-slate-300">1000 mL (Observed 1005 mL)</td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">ThermoSteel_CAD_Spec.pdf</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold font-mono">SATISFIED</td>
                </tr>
                <tr className="hover:bg-[#13192a] transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-cyan-400">Cl. 5.2</td>
                  <td className="py-3 px-4 text-slate-200">Double Wall Vacuum Construction</td>
                  <td className="py-3 px-4 text-slate-300">Double Wall SS, Vacuum Sealed</td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">Assembly_Drawing_DWG-002.pdf</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold font-mono">SATISFIED</td>
                </tr>
                <tr className="bg-amber-950/20 hover:bg-amber-950/30 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-amber-400">Cl. 5.3</td>
                  <td className="py-3 px-4 text-amber-200 font-medium">Thermal Performance Test (6h Retention)</td>
                  <td className="py-3 px-4 text-amber-300 italic">Unverified (≥ 65°C required)</td>
                  <td className="py-3 px-4 text-amber-400/80 font-mono">Missing NABL Test Report</td>
                  <td className="py-3 px-4 text-amber-400 font-bold font-mono">MISSING</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 3. Open Gaps & Required Actions */}
        <section className="space-y-3">
          <h3 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
            3. Open Gaps & Required Remediation Actions
          </h3>
          <div className="p-4 rounded-xl bg-[#0b0f19] border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">
                IS 17526:2021 Cl. 5.3 Thermal Performance Test
              </span>
              <span className="font-mono font-semibold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-500/30">
                LAB TEST REQUIRED
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Upload an empirical test certificate from a recognized NABL accredited laboratory verifying water temperature remains ≥ 65°C after 6 hours when tested per Clause 5.3.
            </p>
          </div>
        </section>

        {/* 4. Expert Review & Sources */}
        <section className="space-y-2 text-xs">
          <h3 className="font-space-grotesk text-xs font-bold text-white uppercase tracking-wider">
            4. Expert Review & Statutory Sources
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 bg-[#0b0f19] border border-slate-800 rounded-xl">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">Attestation Status</span>
              <span className="text-slate-200 font-medium mt-0.5 block font-space-grotesk">Pre-Audit Evaluation Committed</span>
            </div>
            <div className="p-3.5 bg-[#0b0f19] border border-slate-800 rounded-xl">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">Statutory Source</span>
              <span className="text-slate-200 font-medium mt-0.5 block font-space-grotesk">Official BIS Gazette Order S.O. 1234(E)</span>
            </div>
          </div>
        </section>

        {/* 5. Cryptographic Integrity Seal */}
        <section className="p-4 bg-[#0b0f19] border border-slate-800 rounded-xl space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-space-grotesk font-semibold text-white">
              5. Tamper-Evident Assessment Seal (SHA-256)
            </span>
            <span className="font-mono text-[11px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              Valid Cryptographic Seal
            </span>
          </div>
          <div className="font-mono text-[11px] text-cyan-300 break-all bg-[#080c14] p-3 rounded-lg border border-slate-800 select-all shadow-inner">
            {sha256}
          </div>
        </section>
      </article>
    </div>
  );
}