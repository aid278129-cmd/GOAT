import React, { useState } from 'react';
import { StatusBadge } from '../StatusBadge';
import { EvidenceGraphCanvas } from '../EvidenceGraphCanvas';

export function EvidenceMatrixView({ assessment, onUploadEvidence, onNavigate }) {
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'graph'
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [snippetText, setSnippetText] = useState('');
  const [evidenceType, setEvidenceType] = useState('TEST_REPORT');
  const [evidenceAuthority, setEvidenceAuthority] = useState('LAB_REPORT');
  const [pageNumber, setPageNumber] = useState(1);
  const [targetClause, setTargetClause] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!assessment) {
    return (
      <div className="flex-1 p-6 md:p-8 flex items-center justify-center font-sans">
        <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto text-slate-500">
            <span className="material-symbols-outlined text-2xl">policy</span>
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">No Evidence Workspace</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Select an assessment or enter product information in Step 1 to manage evidence documents and test certificates.
            </p>
          </div>
          <button
            onClick={() => onNavigate('input')}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition cursor-pointer"
          >
            Go to Product Input
          </button>
        </div>
      </div>
    );
  }

  const evidenceList = assessment.evidence || [];
  const requirements = assessment.requirements || assessment.clauses || [];

  const handleEvidenceSubmit = async (e) => {
    e.preventDefault();
    if (!snippetText.trim()) return;
    setIsSubmitting(true);
    try {
      await onUploadEvidence(snippetText.trim(), evidenceType, evidenceAuthority, pageNumber);
      setSnippetText('');
      setShowUploadForm(false);
    } catch (err) {
      console.error('Evidence upload error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 p-6 md:p-8 space-y-6 overflow-y-auto font-sans bg-[#F8FAFC]">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
              Step 05 / 08 &bull; Evidence Firewall & Verification
            </span>
            <span className="text-xs text-slate-500">Document Artifacts & Test Certificate Verification</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Evidence Audit Matrix</span>
            <span className="text-xs font-mono font-normal text-slate-500">[{assessment.assessment_number || assessment.assessment_id?.slice(0, 8)}]</span>
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Audit trail validating lab certificates, test readings, and manufacturer drawings against clause requirements.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex bg-slate-200/70 p-0.5 rounded text-xs font-mono">
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                viewMode === 'table' ? 'bg-white font-bold text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Matrix Table
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                viewMode === 'graph' ? 'bg-white font-bold text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Relationship Graph
            </button>
          </div>
          <button
            onClick={() => setShowUploadForm(!showUploadForm)}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span className="material-symbols-outlined text-[15px]">upload_file</span>
            <span>Attach Evidence</span>
          </button>
          <button
            onClick={() => onNavigate('gaps')}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
          >
            <span>Proceed to Compliance Gaps</span>
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Cardinal Invariant Banner: USER CLAIM != VERIFIED EVIDENCE != COMPLIANCE RESULT */}
      <div className="p-4 rounded-lg bg-slate-900 text-white shadow-2xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
            Evidence Verification Principle
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-slate-700">
            Strict Integrity Rule
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2 md:gap-4 text-xs font-mono font-bold py-1">
          <span className="px-2.5 py-1 rounded bg-slate-800 text-amber-300 border border-slate-700">
            USER CLAIM
          </span>
          <span className="text-slate-500 text-base">&ne;</span>
          <span className="px-2.5 py-1 rounded bg-slate-800 text-sky-300 border border-slate-700">
            VERIFIED EVIDENCE
          </span>
          <span className="text-slate-500 text-base">&ne;</span>
          <span className="px-2.5 py-1 rounded bg-slate-800 text-emerald-300 border border-slate-700">
            COMPLIANCE RESULT
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
          Uploading a document does not automatically grant compliance. Evidence is classified by authority level: only genuine NABL/BIS accredited test certificates satisfy test-bound clauses. Unverified user statements remain in non-authoritative status.
        </p>
      </div>

      {/* Upload / Attach Evidence Drawer Form */}
      {showUploadForm && (
        <form onSubmit={handleEvidenceSubmit} className="p-4 rounded-lg bg-white border border-indigo-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Attach Test Certificate Snippet / Laboratory Finding
            </h2>
            <button
              type="button"
              onClick={() => setShowUploadForm(false)}
              className="text-slate-400 hover:text-slate-700 text-xs font-mono"
            >
              [Cancel]
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Evidence Type</label>
              <select
                value={evidenceType}
                onChange={(e) => setEvidenceType(e.target.value)}
                className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs bg-slate-50 focus:border-slate-900 focus:outline-none"
              >
                <option value="TEST_REPORT">Accredited Laboratory Test Report</option>
                <option value="MANUFACTURER_SPEC">Manufacturer Specification Sheet</option>
                <option value="MATERIAL_TEST_CERT">Material Mill Test Certificate (MTC)</option>
                <option value="PHOTO_MARKING">Product Rating Plate Photo</option>
                <option value="OTHER_DOCUMENT">Technical Drawing / BOM</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Authority Level</label>
              <select
                value={evidenceAuthority}
                onChange={(e) => setEvidenceAuthority(e.target.value)}
                className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs bg-slate-50 focus:border-slate-900 focus:outline-none"
              >
                <option value="LAB_REPORT">NABL / Accredited Laboratory Report</option>
                <option value="MANUFACTURER_DOC">Manufacturer Internal Documentation</option>
                <option value="USER_STATEMENT">User Provided Statement (Unverified)</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-500 mb-1">Report Page Reference</label>
              <input
                type="number"
                min="1"
                value={pageNumber}
                onChange={(e) => setPageNumber(parseInt(e.target.value) || 1)}
                className="w-full px-2.5 py-1.5 border border-slate-300 rounded text-xs bg-slate-50 focus:border-slate-900 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-500 mb-1">
              Verbatim Finding / Extracted Metric
            </label>
            <textarea
              rows="3"
              placeholder="e.g. Inversion Leakage Test Clause 5.2: 10 minute inverted test completed at 0.5 bar pressure with zero water droplet egress observed. Certified by NABL Lab #TC-8891."
              value={snippetText}
              onChange={(e) => setSnippetText(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded text-xs bg-slate-50 focus:border-slate-900 focus:outline-none font-mono"
            ></textarea>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setShowUploadForm(false)}
              className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded text-xs font-semibold hover:bg-slate-200 transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !snippetText.trim()}
              className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded text-xs font-semibold transition cursor-pointer"
            >
              {isSubmitting ? 'Evaluating...' : 'Submit & Recalculate Gaps'}
            </button>
          </div>
        </form>
      )}

      {/* View Mode: Graph or Table */}
      {viewMode === 'graph' ? (
        <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden h-[540px]">
          <div className="px-4 py-2.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Compliance Evidence Relationship Graph
            </span>
            <span className="text-[11px] font-mono text-slate-500">Product &rarr; Standard &rarr; Clause &rarr; Evidence &rarr; Gap</span>
          </div>
          <div className="h-[490px]">
            <EvidenceGraphCanvas graphData={assessment.evidence_graph} />
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-slate-600 text-sm">fact_check</span>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Evidence Matrix Ledger
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            {evidenceList.length} Evidence Artifacts Attached
          </span>
        </div>

        {evidenceList.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 space-y-2">
            <p className="font-semibold text-slate-700">No evidence documents attached to this assessment.</p>
            <p className="text-slate-400 max-w-sm mx-auto">
              Attach test reports or manufacturer specifications using the button above to satisfy clause requirements and close compliance gaps.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-600 font-mono text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-4">Evidence ID / Source</th>
                  <th className="py-2.5 px-4">Extracted Snippet & Verbatim Finding</th>
                  <th className="py-2.5 px-4">Authority Class</th>
                  <th className="py-2.5 px-4">Page Ref</th>
                  <th className="py-2.5 px-4 text-right">Verification Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {evidenceList.map((ev, idx) => {
                  const evId = ev.id || `EV-${idx + 1}`;
                  const snippet = ev.snippet || ev.text || ev.content || 'Evidence snippet recorded';
                  const source = ev.source || ev.source_file || 'Test Document';
                  const auth = ev.authority || ev.authority_level || 'LAB_REPORT';
                  const page = ev.page || ev.page_number || '—';
                  const status = ev.verification_status || (auth === 'LAB_REPORT' ? 'VERIFIED' : 'USER_PROVIDED');

                  return (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono">
                        <span className="font-bold text-slate-900">{evId}</span>
                        <span className="block text-[10px] text-slate-400 truncate max-w-[140px]" title={source}>
                          {source}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700 max-w-md">
                        <p className="line-clamp-2 leading-relaxed" title={snippet}>
                          {snippet}
                        </p>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-600">
                        {auth}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                        p. {page}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {status === 'VERIFIED' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            VERIFIED
                          </span>
                        )}
                        {status === 'USER_PROVIDED' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-sky-500"></span>
                            USER_PROVIDED
                          </span>
                        )}
                        {status !== 'VERIFIED' && status !== 'USER_PROVIDED' && (
                          <StatusBadge status={status} />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      )}
    </div>
  );
}
