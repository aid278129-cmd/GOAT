import React, { useState } from 'react';
import {
  ShieldCheck,
  FileText,
  CheckCircle2,
  Bookmark,
  ExternalLink,
  AlertTriangle,
  Hash,
  Layers,
  Lock,
  XCircle,
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export function CitationViewer() {
  const [selectedCase, setSelectedCase] = useState('verified');

  const sampleCases = {
    verified: {
      claim: 'Product satisfies thermal retention requirements under IS 17526:2021 Clause 5.4.',
      source_id: 'DOC-NABL-REPORT-2024-01',
      source_name: 'National Accreditation Board (NABL) Test Certificate #TC-8812',
      source_authority: 'NABL_ACCREDITED_LAB',
      standard: 'IS 17526:2021',
      clause: 'Clause 5.4 (Thermal Retention)',
      page: 4,
      evidence_id: 'EV-LAB-001',
      evidence_text:
        'Container filled with water at 95°C; stabilized ambient 20°C. Temperature measured after 6 hours was 66.5°C (required >= 60.0°C). Result: PASS.',
      evidence_hash: '7a8f6d2e9b1c4a5e3f8d2b7c1a9e4f6d8b2c1a3e5f7d9b1c3a5e7f9d1b3c5a7e',
      verification_status: 'VERIFIED_LAB_REPORT',
      knowledge_version: 'v1.2.0-gazette-verified',
      validation_result: 'VERIFIED',
      failure_reason: null,
      trust_chain: [
        { label: 'CLAIM', value: 'Thermal Retention >= 60°C' },
        { label: 'SOURCE', value: 'NABL Test Cert #TC-8812' },
        { label: 'STANDARD', value: 'IS 17526:2021' },
        { label: 'CLAUSE', value: 'Clause 5.4 (p. 4)' },
        { label: 'EVIDENCE', value: 'EV-LAB-001 (66.5°C)' },
        { label: 'VERIFICATION', value: 'SHA-256 Matched' },
        { label: 'DECISION', value: 'VERIFIED' },
      ],
    },
    cross_standard: {
      claim: 'Immersion heater meets drop resistance standards.',
      source_id: 'DOC-DOMESTIC-FLASK-01',
      source_name: 'Vacuum Flask Drop Certificate',
      source_authority: 'THIRD_PARTY_LAB',
      standard: 'IS 302-2-201:2008',
      clause: 'Clause 22.101',
      page: 2,
      evidence_id: 'EV-FLASK-DROP',
      evidence_text: 'Container dropped from 1.0 m onto hardwood floor.',
      evidence_hash: 'c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2',
      verification_status: 'REJECTED',
      knowledge_version: 'v1.2.0-gazette-verified',
      validation_result: 'REJECTED',
      failure_reason:
        'Cross-Standard Evidence Leakage: Evidence document references IS 17526:2021, which does not match required applicable standard IS 302-2-201:2008.',
      trust_chain: [
        { label: 'CLAIM', value: 'Drop Resistance' },
        { label: 'SOURCE', value: 'Vacuum Flask Doc' },
        { label: 'STANDARD', value: 'IS 302-2-201:2008' },
        { label: 'CLAUSE', value: 'Clause 22.101' },
        { label: 'EVIDENCE', value: 'WRONG STANDARD' },
        { label: 'VERIFICATION', value: 'LEAKAGE DETECTED' },
        { label: 'DECISION', value: 'BLOCKED' },
      ],
    },
    user_claim: {
      claim: 'Inner liner is constructed of Grade 304 Stainless Steel.',
      source_id: 'DOC-MARKETING-BROCHURE',
      source_name: 'Product Amazon Product Listing / Marketing Brochure',
      source_authority: 'UNVERIFIED_MANUFACTURER_CLAIM',
      standard: 'IS 17526:2021',
      clause: 'Clause 4.2.1',
      page: 1,
      evidence_id: 'EV-USER-CLAIM',
      evidence_text: '"Made with premium rust-proof 304 food-grade stainless steel for longevity."',
      evidence_hash: '9e107d9d372bb6826bd81d3542a419d6dae2ee1d314845249fbb0ce01cf6fedc',
      verification_status: 'USER_CLAIM',
      knowledge_version: 'v1.2.0-gazette-verified',
      validation_result: 'REJECTED',
      failure_reason:
        'Unverified Source Provenance [USER_CLAIM]: Marketing statements and manufacturer claims cannot serve as authoritative compliance evidence. Mill Test Certificate (MTC) required.',
      trust_chain: [
        { label: 'CLAIM', value: 'Grade 304 SS Liner' },
        { label: 'SOURCE', value: 'Amazon Listing' },
        { label: 'STANDARD', value: 'IS 17526:2021' },
        { label: 'CLAUSE', value: 'Clause 4.2.1' },
        { label: 'EVIDENCE', value: 'USER_CLAIM' },
        { label: 'VERIFICATION', value: 'UNVERIFIED' },
        { label: 'DECISION', value: 'BLOCKED' },
      ],
    },
    tampered_hash: {
      claim: 'Electric immersion heater leakage current within statutory limit.',
      source_id: 'DOC-TAMPERED-REPORT',
      source_name: 'Modified Lab Report Excerpt',
      source_authority: 'UNAUTHORIZED_ALTERATION',
      standard: 'IS 302-2-201:2008',
      clause: 'Clause 13.1',
      page: 6,
      evidence_id: 'EV-TAMPERED-01',
      evidence_text: 'Measured operating leakage current: 0.15 mA (limit <= 0.75 mA).',
      evidence_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      verification_status: 'TAMPERED',
      knowledge_version: 'v1.2.0-gazette-verified',
      validation_result: 'REJECTED',
      failure_reason:
        'Cryptographic Integrity Failure: SHA-256 digest mismatch. Computed hash does not match recorded certificate hash. Tampering detected.',
      trust_chain: [
        { label: 'CLAIM', value: 'Leakage Current <= 0.75mA' },
        { label: 'SOURCE', value: 'Altered Excerpt' },
        { label: 'STANDARD', value: 'IS 302-2-201:2008' },
        { label: 'CLAUSE', value: 'Clause 13.1' },
        { label: 'EVIDENCE', value: 'HASH MISMATCH' },
        { label: 'VERIFICATION', value: 'DIGEST INVALID' },
        { label: 'DECISION', value: 'BLOCKED' },
      ],
    },
  };

  const current = sampleCases[selectedCase];

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
      {/* Header & Invariants */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">
              Layer 8: Source Validation & Citation Guard
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-mono font-bold">
              0% LLM Authority Guaranteed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Primary Rule: <strong className="text-slate-800 font-mono">NO VERIFIED SOURCE → NO REGULATORY CLAIM</strong>. Every claim is strictly validated against Gazette knowledge, document provenance, and cryptographic SHA-256 hashes.
          </p>
        </div>

        {/* Case Toggle Buttons */}
        <div className="flex flex-wrap gap-1.5 p-1 rounded-lg bg-slate-100 border border-slate-200">
          <button
            onClick={() => setSelectedCase('verified')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition cursor-pointer ${
              selectedCase === 'verified'
                ? 'bg-white text-emerald-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ✓ Verified Citation
          </button>
          <button
            onClick={() => setSelectedCase('cross_standard')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition cursor-pointer ${
              selectedCase === 'cross_standard'
                ? 'bg-white text-red-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ✕ Cross-Standard Leakage
          </button>
          <button
            onClick={() => setSelectedCase('user_claim')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition cursor-pointer ${
              selectedCase === 'user_claim'
                ? 'bg-white text-amber-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ✕ User Claim Rejection
          </button>
          <button
            onClick={() => setSelectedCase('tampered_hash')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold transition cursor-pointer ${
              selectedCase === 'tampered_hash'
                ? 'bg-white text-rose-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ✕ Hash Tampering
          </button>
        </div>
      </div>

      {/* Trust Chain Visualization */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-600" />
            Machine-Readable Provenance Chain
          </span>
          <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold ${
            current.validation_result === 'VERIFIED'
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : 'bg-red-100 text-red-800 border border-red-300'
          }`}>
            DECISION: {current.validation_result}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {current.trust_chain.map((step, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-lg border text-center space-y-1 ${
                current.validation_result === 'VERIFIED'
                  ? 'bg-white border-emerald-200 text-slate-800'
                  : idx >= 4
                  ? 'bg-red-50/80 border-red-200 text-red-900'
                  : 'bg-white border-slate-200 text-slate-800'
              }`}
            >
              <div className="text-[9px] font-mono uppercase text-slate-500 font-bold">
                {step.label}
              </div>
              <div className="text-[11px] font-semibold truncate" title={step.value}>
                {step.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-xs">
        {/* Left: Claim & Standard */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2 font-semibold text-indigo-700">
              <FileText className="w-4 h-4 text-indigo-600" />
              Claim & BIS Standard Citation
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              Knowledge: {current.knowledge_version}
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <span className="text-slate-500 text-[10px] uppercase block">Submitted Regulatory Claim:</span>
              <p className="font-semibold text-slate-900 mt-0.5">"{current.claim}"</p>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="text-slate-400 block text-[9px]">Standard</span>
                <strong className="text-indigo-700">{current.standard}</strong>
              </div>
              <div className="p-2 rounded bg-white border border-slate-200">
                <span className="text-slate-400 block text-[9px]">Clause & Page</span>
                <strong className="text-amber-700">{current.clause} (p. {current.page})</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Evidence Provenance & Cryptographic Digest */}
        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2 font-semibold text-emerald-700">
              <Lock className="w-4 h-4 text-emerald-600" />
              Evidence Provenance & SHA-256 Digest
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              {current.source_authority}
            </span>
          </div>

          <div className="space-y-2">
            <div>
              <span className="text-slate-500 text-[10px] uppercase block">Evidence Excerpt:</span>
              <p className="font-mono text-slate-800 bg-white p-2.5 rounded border border-slate-200 text-[11px] leading-relaxed">
                {current.evidence_text}
              </p>
            </div>

            <div className="p-2 rounded bg-white border border-slate-200 font-mono text-[10px] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 flex items-center gap-1">
                  <Hash className="w-3 h-3" /> SHA-256 Digest:
                </span>
                <span className="text-slate-400">{current.evidence_id}</span>
              </div>
              <div className="text-slate-800 truncate text-[9px]" title={current.evidence_hash}>
                {current.evidence_hash}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Failure Reason Alert (When Rejected) */}
      {current.failure_reason && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 space-y-1 text-xs">
          <div className="flex items-center gap-2 font-bold text-red-800">
            <XCircle className="w-4 h-4 text-red-600" />
            Layer 8 Hard Rejection Enforced
          </div>
          <p className="text-red-700 text-[11px] leading-relaxed pl-6">
            {current.failure_reason}
          </p>
          <div className="text-[10px] font-mono text-red-600 pl-6 pt-1">
            Action: Claim actively suppressed from Layer 9 final output.
          </div>
        </div>
      )}
    </div>
  );
}
