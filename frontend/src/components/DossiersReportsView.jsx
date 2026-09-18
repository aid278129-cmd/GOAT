import React, { useState, useEffect, useCallback } from 'react';
import { dossierApi, jobsApi } from '../api';

export function DossiersReportsView({ jobId: propJobId, onNavigateJobs }) {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(propJobId || '');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('passport'); // passport | dossiers | traceability | integrity

  // Data states
  const [passportData, setPassportData] = useState(null);
  const [dossiersList, setDossiersList] = useState([]);
  const [selectedDossier, setSelectedDossier] = useState(null);
  const [activeSectionNum, setActiveSectionNum] = useState(1);
  const [traceabilityRows, setTraceabilityRows] = useState([]);
  const [traceFilter, setTraceFilter] = useState('');
  const [integrityData, setIntegrityData] = useState(null);
  const [feedback, setFeedback] = useState(null);

  // Load available jobs on mount
  useEffect(() => {
    async function fetchJobs() {
      try {
        const jList = await jobsApi.listJobs();
        setJobs(jList || []);
        if (!selectedJobId && jList && jList.length > 0) {
          setSelectedJobId(jList[0].id);
        }
      } catch (err) {
        console.error('Failed to load jobs list:', err);
      }
    }
    fetchJobs();
  }, []);

  useEffect(() => {
    if (propJobId) {
      setSelectedJobId(propJobId);
    }
  }, [propJobId]);

  // Load all dossier/passport data when selectedJobId changes
  const loadJobData = useCallback(async (jobId) => {
    if (!jobId) return;
    setLoading(true);
    setFeedback(null);
    try {
      const [pRes, dList, tRes, iRes] = await Promise.all([
        dossierApi.getPassport(jobId).catch(() => null),
        dossierApi.listDossiers(jobId).catch(() => []),
        dossierApi.getTraceability(jobId).catch(() => ({ matrix: [] })),
        dossierApi.getIntegrity(jobId).catch(() => null),
      ]);

      setPassportData(pRes);
      setDossiersList(dList || []);
      setTraceabilityRows(tRes?.matrix || []);
      setIntegrityData(iRes);

      // Select latest dossier if available
      if (dList && dList.length > 0) {
        const detail = await dossierApi.getDossier(jobId, dList[0].id).catch(() => null);
        setSelectedDossier(detail);
      } else {
        setSelectedDossier(null);
      }
    } catch (err) {
      console.error('Failed to load dossier data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      loadJobData(selectedJobId);
    }
  }, [selectedJobId, loadJobData]);

  // Handle generating a new dossier version
  const handleGenerateDossier = async () => {
    if (!selectedJobId) return;
    setGenerating(true);
    setFeedback(null);
    try {
      const res = await dossierApi.generateDossier(selectedJobId);
      if (res.is_newly_generated) {
        setFeedback({
          type: 'success',
          message: `Dossier v${res.version} successfully compiled and cryptographically registered!`,
        });
      } else {
        setFeedback({
          type: 'info',
          message: `Source state unchanged. Returned existing immutable Dossier v${res.version} (Idempotent).`,
        });
      }
      await loadJobData(selectedJobId);
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err?.data?.detail || err.message || 'Failed to generate dossier.',
      });
    } finally {
      setGenerating(false);
    }
  };

  // Handle selecting a specific dossier version to inspect
  const handleSelectDossier = async (dossierId) => {
    if (!selectedJobId || !dossierId) return;
    try {
      const detail = await dossierApi.getDossier(selectedJobId, dossierId);
      setSelectedDossier(detail);
      setActiveSectionNum(1);
    } catch (err) {
      console.error('Failed to load dossier details:', err);
    }
  };

  // Handle downloading PDF
  const handleDownloadPdf = async (dossierId, title) => {
    if (!selectedJobId || !dossierId) return;
    try {
      await dossierApi.downloadDossierPdf(selectedJobId, dossierId, `${title || 'Regulatory_Dossier'}.pdf`);
    } catch (err) {
      alert(`PDF download failed: ${err.message}`);
    }
  };

  // Filtered traceability rows
  const filteredTraceRows = traceabilityRows.filter((r) => {
    if (!traceFilter) return true;
    const term = traceFilter.toLowerCase();
    return (
      (r.requirement_id && r.requirement_id.toLowerCase().includes(term)) ||
      (r.clause && r.clause.toLowerCase().includes(term)) ||
      (r.parameter_key && r.parameter_key.toLowerCase().includes(term)) ||
      (r.assessment_state && r.assessment_state.toLowerCase().includes(term))
    );
  });

  const states = passportData?.passport_states || {};

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 font-sans">
      {/* Top Header & Job Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
              Regulatory Dossier &amp; Compliance Passport Center
            </h1>
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
              Phase 5 Production
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
            Immutable snapshot dossiers, deterministic traceability, and honest multi-dimensional regulatory passports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Job Selection Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#64748B] font-semibold">Active Job:</span>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="text-xs font-medium bg-white border border-[#CBD5E1] rounded px-2.5 py-1.5 text-[#0F172A] focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-xs"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.job_number} — {j.product_name || j.title}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={handleGenerateDossier}
            disabled={generating || !selectedJobId}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-[#1D4ED8] hover:bg-[#1E40AF] disabled:bg-slate-300 rounded transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">
              {generating ? 'hourglass_top' : 'verified'}
            </span>
            {generating ? 'Compiling Dossier...' : 'Compile New Dossier'}
          </button>
        </div>
      </div>

      {/* Statutory Disclaimer Banner */}
      <div className="p-3.5 rounded-lg bg-amber-50/80 border border-amber-200 flex items-start gap-2.5 text-xs text-amber-900">
        <span className="material-symbols-outlined text-base text-amber-700 shrink-0 mt-0.5">
          policy
        </span>
        <div className="space-y-0.5">
          <span className="font-bold uppercase tracking-wider text-[11px] text-amber-800">
            Statutory Regulatory Notice
          </span>
          <p className="text-amber-950/80 leading-relaxed text-[11px]">
            Zyntrix provides deterministic engineering assessment, evidence traceability, and technical documentation.
            This workstation does <strong>NOT</strong> grant BIS certification, statutory licenses, or laboratory approvals.
            Conformity must be submitted directly to the Bureau of Indian Standards through official statutory channels.
          </p>
        </div>
      </div>

      {/* Alert / Feedback Notification */}
      {feedback && (
        <div
          className={`p-3 rounded-md text-xs font-medium flex items-center justify-between border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : feedback.type === 'info'
              ? 'bg-blue-50 text-blue-800 border-blue-200'
              : 'bg-rose-50 text-rose-800 border-rose-200'
          }`}
        >
          <span>{feedback.message}</span>
          <button
            type="button"
            onClick={() => setFeedback(null)}
            className="text-xs font-bold px-1 text-slate-500 hover:text-slate-800"
          >
            &times;
          </button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-[#E2E8F0]">
        {[
          { id: 'passport', label: 'Compliance Passport', icon: 'badge' },
          { id: 'dossiers', label: 'Dossier Snapshots & Viewer', icon: 'menu_book' },
          { id: 'traceability', label: 'Traceability Matrix', icon: 'timeline' },
          { id: 'integrity', label: 'Cryptographic Integrity', icon: 'lock_reset' },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
                isActive
                  ? 'border-[#1D4ED8] text-[#1D4ED8]'
                  : 'border-transparent text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              <span className="material-symbols-outlined text-sm">{tab.icon}</span>
              {tab.label}
              {tab.id === 'dossiers' && dossiersList.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-slate-100 text-slate-600 font-mono">
                  {dossiersList.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB 1: COMPLIANCE PASSPORT */}
      {activeTab === 'passport' && (
        <div className="flex flex-col gap-6">
          {/* Passport Header Card */}
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E2E8F0] pb-4">
              <div>
                <span className="font-mono text-[10px] text-[#64748B] uppercase tracking-wider font-semibold">
                  Official Technical Evaluation Passport
                </span>
                <h2 className="text-lg sm:text-xl font-bold text-[#0F172A] mt-0.5">
                  {passportData?.product_name || 'Selected Product'}
                </h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-[#64748B] mt-1">
                  <span>Model: <strong>{passportData?.model_number || 'N/A'}</strong></span>
                  <span>&bull;</span>
                  <span>Manufacturer: <strong>{passportData?.manufacturer || 'N/A'}</strong></span>
                  <span>&bull;</span>
                  <span>Job Number: <strong>{passportData?.job_number}</strong></span>
                </div>
              </div>

              <div className="text-right font-mono text-xs space-y-1 self-start sm:self-auto">
                <div className="text-[11px] text-[#64748B]">
                  Latest Dossier:{' '}
                  <strong className="text-blue-700 font-semibold">
                    {passportData?.latest_dossier_version ? `v${passportData.latest_dossier_version}` : 'None compiled'}
                  </strong>
                </div>
                {passportData?.latest_dossier_digest && (
                  <div className="text-[10px] text-slate-400 truncate max-w-xs" title={passportData.latest_dossier_digest}>
                    SHA: {passportData.latest_dossier_digest.slice(0, 18)}...
                  </div>
                )}
              </div>
            </div>

            {/* 8-Dimensional Honest State Breakdown */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#0F172A]">
                  Multi-Dimensional Regulatory &amp; Engineering State
                </h3>
                <span className="text-[11px] text-[#64748B] font-mono">
                  Independently Evaluated
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StateBadge title="Scope State" state={states.scope_state} />
                <StateBadge title="Evidence State" state={states.evidence_state} />
                <StateBadge title="DNA State" state={states.dna_state} />
                <StateBadge title="Assessment State" state={states.assessment_state} />
                <StateBadge title="Review State" state={states.review_state} />
                <StateBadge title="Attestation State" state={states.attestation_state} />
                <StateBadge title="Finding State" state={states.finding_state} />
                <StateBadge title="Dossier State" state={states.dossier_state} />
              </div>
            </div>

            {/* Metrics Counters Grid */}
            <div className="pt-3 border-t border-[#E2E8F0] grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-center">
              <CounterBox label="Standards" val={states.counts?.standards_count ?? 0} />
              <CounterBox label="Clauses" val={states.counts?.requirements_count ?? 0} />
              <CounterBox label="Accepted Ev" val={states.counts?.accepted_evidence ?? 0} />
              <CounterBox label="Verified DNA" val={states.counts?.verified_dna_parameters ?? 0} />
              <CounterBox label="Passes" val={states.counts?.engineering_pass_count ?? 0} textClass="text-emerald-700" />
              <CounterBox label="Gaps" val={states.counts?.engineering_gap_count ?? 0} textClass="text-rose-700" />
              <CounterBox label="Pending Rev" val={states.counts?.pending_reviews ?? 0} textClass="text-amber-700" />
              <CounterBox label="Attestations" val={states.counts?.active_attestations_count ?? 0} textClass="text-blue-700" />
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DOSSIER SNAPSHOTS & DOCUMENT VIEWER */}
      {activeTab === 'dossiers' && (
        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Left Column: Version History */}
          <div className="w-full lg:w-72 bg-white border border-[#E2E8F0] rounded-xl p-4 shadow-xs shrink-0 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#E2E8F0]">
              <span className="font-mono text-xs font-bold text-[#0F172A] uppercase tracking-wider">
                Dossier Versions
              </span>
              <span className="text-[11px] font-mono text-[#64748B]">
                {dossiersList.length} Archived
              </span>
            </div>

            {dossiersList.length === 0 ? (
              <div className="py-6 text-center text-xs text-[#64748B]">
                No dossiers compiled yet. Click "Compile New Dossier" to create v1.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {dossiersList.map((dos) => {
                  const isSelected = selectedDossier?.id === dos.id;
                  return (
                    <button
                      key={dos.id}
                      type="button"
                      onClick={() => handleSelectDossier(dos.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-blue-50 border-blue-300 text-blue-900'
                          : 'bg-white border-[#E2E8F0] hover:bg-slate-50 text-[#0F172A]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs">v{dos.version}</span>
                        <span className="font-mono text-[10px] text-[#64748B]">
                          {dos.generated_at ? new Date(dos.generated_at).toLocaleDateString() : ''}
                        </span>
                      </div>
                      <div className="text-[11px] truncate text-[#64748B] mt-0.5">{dos.title}</div>
                      <div className="font-mono text-[9px] text-slate-400 mt-1 truncate">
                        SHA: {dos.dossier_digest ? dos.dossier_digest.slice(0, 16) : ''}...
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: 20-Section Document Viewer */}
          <div className="flex-1 w-full bg-white border border-[#E2E8F0] rounded-xl p-5 sm:p-6 shadow-xs flex flex-col gap-5">
            {selectedDossier ? (
              <>
                {/* Dossier Control Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E2E8F0]">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold">
                        v{selectedDossier.version}
                      </span>
                      <h2 className="text-base sm:text-lg font-bold text-[#0F172A]">
                        {selectedDossier.title}
                      </h2>
                    </div>
                    <div className="font-mono text-[11px] text-[#64748B] mt-1 space-x-3">
                      <span>ID: {selectedDossier.id}</span>
                      <span>&bull;</span>
                      <span>Engine: {selectedDossier.assessment_engine_version}</span>
                      <span>&bull;</span>
                      <span>By: {selectedDossier.generated_by_email}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleDownloadPdf(selectedDossier.id, selectedDossier.title)}
                    className="px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded transition-colors flex items-center gap-1.5 shadow-sm self-start sm:self-auto cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm">download</span>
                    Download Authoritative PDF
                  </button>
                </div>

                {/* 20-Section Selector Tabs / Pills */}
                <div className="flex items-center gap-1 overflow-x-auto pb-2 border-b border-slate-100 text-xs">
                  {selectedDossier.sections?.map((sec) => (
                    <button
                      key={sec.section_number}
                      type="button"
                      onClick={() => setActiveSectionNum(sec.section_number)}
                      className={`px-2.5 py-1 rounded text-[11px] font-mono whitespace-nowrap transition-colors cursor-pointer ${
                        activeSectionNum === sec.section_number
                          ? 'bg-[#1D4ED8] text-white font-bold'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {sec.section_number}. {sec.title.split('/')[0]}
                    </button>
                  ))}
                </div>

                {/* Active Section Content Renderer */}
                <div className="pt-2">
                  {selectedDossier.sections?.filter((s) => s.section_number === activeSectionNum).map((s) => (
                    <div key={s.section_number} className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-bold text-[#0F172A]">
                          {s.section_number}. {s.title}
                        </h3>
                        <span className="font-mono text-[11px] text-[#64748B]">
                          Key: {s.section_key}
                        </span>
                      </div>

                      <SectionContentDisplay sectionKey={s.section_key} content={s.content_json} />
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">
                No dossier selected. Compile or select a version to inspect.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: TRACEABILITY MATRIX */}
      {activeTab === 'traceability' && (
        <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0F172A] font-mono">
                Statutory Traceability Matrix
              </h2>
              <p className="text-xs text-[#64748B] mt-0.5">
                Deterministic lineage: Requirement &rarr; Product DNA &rarr; Evidence &rarr; CAD &rarr; Assessment &rarr; Finding &rarr; Review &rarr; Attestation.
              </p>
            </div>

            <input
              type="text"
              placeholder="Filter by clause, parameter, or status..."
              value={traceFilter}
              onChange={(e) => setTraceFilter(e.target.value)}
              className="text-xs font-mono px-3 py-1.5 border border-[#CBD5E1] rounded bg-[#F8FAFC] text-[#0F172A] w-full sm:w-72 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-[#E2E8F0] rounded">
              <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0] font-mono text-[11px] text-[#64748B] uppercase">
                <tr>
                  <th className="p-2.5">Requirement / Clause</th>
                  <th className="p-2.5">Product DNA Fact</th>
                  <th className="p-2.5">Supporting Evidence</th>
                  <th className="p-2.5">CAD Telemetry</th>
                  <th className="p-2.5">Assessment Result</th>
                  <th className="p-2.5">Review Decision</th>
                  <th className="p-2.5">Attestation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {filteredTraceRows.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="p-4 text-center text-slate-400 font-mono text-xs">
                      No matching traceability records found.
                    </td>
                  </tr>
                ) : (
                  filteredTraceRows.map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-2.5 font-medium">
                        <div className="font-bold text-[#0F172A]">{r.requirement_id}</div>
                        <div className="font-mono text-[11px] text-[#64748B]">Clause {r.clause}</div>
                      </td>
                      <td className="p-2.5">
                        <div className="font-mono text-[11px] font-semibold text-slate-800">{r.parameter_key}</div>
                        <div className="text-[11px] text-slate-600">{r.dna_value}</div>
                      </td>
                      <td className="p-2.5 font-mono text-[10px]">
                        <div>ID: {r.evidence_id}</div>
                        <div className="text-slate-500">Status: <strong>{r.evidence_acceptance}</strong></div>
                      </td>
                      <td className="p-2.5 font-mono text-[10px]">
                        {r.cad_measurement_id !== 'N/A' ? (
                          <>
                            <div className="text-blue-700 font-semibold">{r.cad_measurement_value}</div>
                            <div className="text-slate-400">{r.cad_measurement_id}</div>
                          </>
                        ) : (
                          <span className="text-slate-400">N/A</span>
                        )}
                      </td>
                      <td className="p-2.5">
                        <span
                          className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            r.assessment_state === 'ENGINEERING_PASS'
                              ? 'bg-emerald-100 text-emerald-800'
                              : r.assessment_state === 'ENGINEERING_GAP'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {r.assessment_state}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono text-[11px]">
                        {r.review_decision !== 'NONE' ? (
                          <span className="font-semibold text-slate-700">{r.review_decision}</span>
                        ) : (
                          <span className="text-slate-400">NONE</span>
                        )}
                      </td>
                      <td className="p-2.5 font-mono text-[11px]">
                        {r.attestation_id !== 'NONE' ? (
                          <span className="text-blue-700 font-semibold">ATT-{r.attestation_id.slice(0, 8)}</span>
                        ) : (
                          <span className="text-slate-400">NONE</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: CRYPTOGRAPHIC INTEGRITY PANEL */}
      {activeTab === 'integrity' && (
        <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0F172A] font-mono">
                Cryptographic Integrity Verification
              </h2>
              <p className="text-xs text-[#64748B] mt-0.5">
                Verifies byte-level SHA-256 integrity of all dossier artifacts against database digests.
              </p>
            </div>

            <span
              className={`px-2.5 py-1 rounded text-xs font-mono font-bold flex items-center gap-1 ${
                integrityData?.is_intact
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-100 text-rose-800 border border-rose-200'
              }`}
            >
              <span className="material-symbols-outlined text-sm">
                {integrityData?.is_intact ? 'verified' : 'gpp_bad'}
              </span>
              {integrityData?.is_intact ? 'ALL ARTIFACTS VERIFIED' : 'INTEGRITY MISMATCH DETECTED'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {integrityData?.dossiers?.map((d) => (
              <div key={d.dossier_id} className="p-4 rounded-lg border border-[#E2E8F0] bg-slate-50/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[#0F172A]">Dossier v{d.version}</span>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      d.is_tamper_free ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {d.is_tamper_free ? 'TAMPER-FREE' : 'INVALID'}
                  </span>
                </div>
                <div className="font-mono text-[10px] text-slate-500 break-all">
                  Canonical Digest: <strong>{d.stored_dossier_digest}</strong>
                </div>

                <div className="pt-2 border-t border-slate-200 space-y-1">
                  <div className="text-[10px] font-mono font-bold text-slate-600 uppercase">Artifacts:</div>
                  {d.artifacts_verified?.map((art) => (
                    <div key={art.artifact_id} className="text-[10px] font-mono bg-white p-2 rounded border border-slate-200">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{art.artifact_type}</span>
                        <span className={art.hash_valid ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>
                          {art.hash_valid ? 'HASH MATCH' : 'MISMATCH'}
                        </span>
                      </div>
                      <div className="text-slate-500 truncate mt-0.5">Stored: {art.stored_hash}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Subcomponents for cleanliness
function StateBadge({ title, state }) {
  const getStyle = (st) => {
    switch (st) {
      case 'DEFINED':
      case 'FULLY_ACCEPTED':
      case 'FULLY_VERIFIED':
      case 'ENGINEERING_PASS':
      case 'COMPLETED':
      case 'ACTIVE':
      case 'RESOLVED':
      case 'GENERATED':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'ENGINEERING_GAP':
      case 'REJECTED_PRESENT':
      case 'CONFLICT_DETECTED':
      case 'REJECTED_ITEMS':
      case 'REVOKED':
      case 'OPEN':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'PARTIALLY_ACCEPTED':
      case 'PARTIALLY_VERIFIED':
      case 'DATA_REQUIRED':
      case 'PENDING':
      case 'WAIVED':
      case 'NEEDS_UPDATE':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className={`p-2.5 rounded-lg border flex flex-col justify-between ${getStyle(state)}`}>
      <span className="text-[10px] font-mono uppercase font-semibold opacity-75">{title}</span>
      <span className="font-mono text-xs font-bold mt-1 tracking-tight truncate">{state || 'NONE'}</span>
    </div>
  );
}

function CounterBox({ label, val, textClass = 'text-[#0F172A]' }) {
  return (
    <div className="p-2 rounded bg-slate-50 border border-slate-100">
      <div className={`text-base font-bold font-mono ${textClass}`}>{val}</div>
      <div className="text-[10px] text-[#64748B] font-medium truncate">{label}</div>
    </div>
  );
}

function SectionContentDisplay({ sectionKey, content }) {
  if (!content) {
    return <div className="text-xs text-slate-400">Empty section.</div>;
  }

  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 text-xs font-mono overflow-x-auto max-h-96">
      <pre className="whitespace-pre-wrap text-[11px] text-slate-800 leading-relaxed">
        {JSON.stringify(content, null, 2)}
      </pre>
    </div>
  );
}
