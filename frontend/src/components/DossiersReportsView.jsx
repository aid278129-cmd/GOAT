import React, { useState, useEffect, useCallback } from 'react';
import { dossierApi, jobsApi } from '../api';
import { GlideSelect } from './loading-ui';

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
        message: `Failed to compile dossier: ${err.message}`,
      });
    } finally {
      setGenerating(false);
    }
  };

  // Handle selecting a specific dossier version from list
  const handleSelectDossier = async (dossierId) => {
    if (!selectedJobId || !dossierId) return;
    try {
      const detail = await dossierApi.getDossier(selectedJobId, dossierId);
      setSelectedDossier(detail);
      setActiveSectionNum(1);
    } catch (err) {
      alert(`Failed to load dossier details: ${err.message}`);
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

  const jobSelectItems = jobs.map((j) => ({
    value: j.id,
    label: `${j.job_number || j.id} — ${j.product_name || j.title || 'Untitled'}`,
  }));

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Top Header & Job Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
              Regulatory Dossier &amp; Compliance Passport Center
            </h1>
            <span className="font-mono text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60">
              Phase 5 Production
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Immutable snapshot dossiers, deterministic traceability, and honest multi-dimensional regulatory passports.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Job Selection Dropdown with GlideSelect */}
          {jobSelectItems.length > 0 && (
            <div className="w-64 sm:w-72">
              <GlideSelect
                items={jobSelectItems}
                value={selectedJobId}
                onChange={(val) => setSelectedJobId(val)}
                placeholder="Select Job"
                width="100%"
              />
            </div>
          )}

          <button
            type="button"
            onClick={handleGenerateDossier}
            disabled={generating || !selectedJobId}
            className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 disabled:opacity-40 rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-cyan-500/10 cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm font-bold">
              {generating ? 'hourglass_top' : 'verified'}
            </span>
            {generating ? 'Compiling Dossier...' : 'Compile New Dossier'}
          </button>
        </div>
      </div>

      {/* Statutory Disclaimer Banner */}
      <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/50 flex items-start gap-3 text-xs text-amber-200">
        <span className="material-symbols-outlined text-base text-amber-400 shrink-0 mt-0.5">
          policy
        </span>
        <div className="space-y-0.5">
          <span className="font-bold uppercase tracking-wider text-[11px] text-amber-300 font-mono">
            Statutory Regulatory Notice
          </span>
          <p className="text-amber-200/80 leading-relaxed text-[11px]">
            GOAT provides deterministic engineering assessment, evidence traceability, and technical documentation.
            This workstation does <strong>NOT</strong> grant BIS certification, statutory licenses, or laboratory approvals.
            Conformity must be submitted directly to the Bureau of Indian Standards through official statutory channels.
          </p>
        </div>
      </div>

      {/* Alert / Feedback Notification */}
      {feedback && (
        <div
          className={`p-3 rounded-lg text-xs font-medium flex items-center justify-between border ${
            feedback.type === 'success'
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
              : feedback.type === 'info'
              ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
              : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
          }`}
        >
          <span>{feedback.message}</span>
          <button
            type="button"
            onClick={() => setFeedback(null)}
            className="text-xs font-bold px-1 text-slate-400 hover:text-slate-200 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
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
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="material-symbols-outlined text-sm">{tab.icon}</span>
              {tab.label}
              {tab.id === 'dossiers' && dossiersList.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono">
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
          <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 sm:p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <span className="font-mono text-[10px] text-cyan-400 uppercase tracking-widest font-semibold">
                  Official Technical Evaluation Passport
                </span>
                <h2 className="text-lg sm:text-xl font-bold text-slate-100 font-['Space_Grotesk'] mt-0.5">
                  {passportData?.product_name || 'Selected Product'}
                </h2>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                  <span>Model: <strong className="text-slate-200">{passportData?.model_number || 'N/A'}</strong></span>
                  <span>&bull;</span>
                  <span>Manufacturer: <strong className="text-slate-200">{passportData?.manufacturer || 'N/A'}</strong></span>
                  <span>&bull;</span>
                  <span>Job Number: <strong className="text-cyan-400">{passportData?.job_number}</strong></span>
                </div>
              </div>

              <div className="text-right font-mono text-xs space-y-1 self-start sm:self-auto">
                <div className="text-[11px] text-slate-400">
                  Latest Dossier:{' '}
                  <strong className="text-cyan-300 font-semibold">
                    {passportData?.latest_dossier_version ? `v${passportData.latest_dossier_version}` : 'None compiled'}
                  </strong>
                </div>
                {passportData?.latest_dossier_digest && (
                  <div className="text-[10px] text-cyan-400/80 truncate max-w-xs" title={passportData.latest_dossier_digest}>
                    SHA: {passportData.latest_dossier_digest.slice(0, 18)}...
                  </div>
                )}
              </div>
            </div>

            {/* 8-Dimensional Honest State Breakdown */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
                  Multi-Dimensional Regulatory &amp; Engineering State
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
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
            <div className="pt-3 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-center">
              <CounterBox label="Standards" val={states.counts?.standards_count ?? 0} />
              <CounterBox label="Clauses" val={states.counts?.requirements_count ?? 0} />
              <CounterBox label="Accepted Ev" val={states.counts?.accepted_evidence ?? 0} />
              <CounterBox label="Verified DNA" val={states.counts?.verified_dna_parameters ?? 0} />
              <CounterBox label="Passes" val={states.counts?.engineering_pass_count ?? 0} textClass="text-emerald-400" />
              <CounterBox label="Gaps" val={states.counts?.engineering_gap_count ?? 0} textClass="text-rose-400" />
              <CounterBox label="Pending Rev" val={states.counts?.pending_reviews ?? 0} textClass="text-amber-400" />
              <CounterBox label="Attestations" val={states.counts?.active_attestations_count ?? 0} textClass="text-cyan-400" />
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DOSSIER SNAPSHOTS & DOCUMENT VIEWER */}
      {activeTab === 'dossiers' && (
        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Left Column: Version History */}
          <div className="w-full lg:w-72 bg-[#0f1422]/90 backdrop-blur-md border border-slate-800 rounded-xl p-4 shadow-xl shrink-0 flex flex-col gap-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider">
                Dossier Versions
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {dossiersList.length} Archived
              </span>
            </div>

            {dossiersList.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
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
                      className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-cyan-950/60 border-cyan-800 text-cyan-200 shadow-inner'
                          : 'bg-slate-900/60 border-slate-800 hover:bg-slate-850 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-cyan-300 font-mono">v{dos.version}</span>
                        <span className="font-mono text-[10px] text-slate-400">
                          {dos.generated_at ? new Date(dos.generated_at).toLocaleDateString() : ''}
                        </span>
                      </div>
                      <div className="text-[11px] truncate text-slate-300 mt-0.5">{dos.title}</div>
                      <div className="font-mono text-[9px] text-slate-500 mt-1 truncate">
                        SHA: {dos.dossier_digest ? dos.dossier_digest.slice(0, 16) : ''}...
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: 20-Section Document Viewer */}
          <div className="flex-1 w-full bg-[#0f1422]/90 backdrop-blur-md border border-slate-800 rounded-xl p-5 sm:p-6 shadow-xl flex flex-col gap-5">
            {selectedDossier ? (
              <>
                {/* Dossier Control Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold">
                        v{selectedDossier.version}
                      </span>
                      <h2 className="text-base sm:text-lg font-bold text-slate-100 font-['Space_Grotesk']">
                        {selectedDossier.title}
                      </h2>
                    </div>
                    <div className="font-mono text-[11px] text-slate-400 mt-1 space-x-3">
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
                    className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-md shadow-cyan-500/20 self-start sm:self-auto cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm font-bold">download</span>
                    Download Authoritative PDF
                  </button>
                </div>

                {/* 20-Section Selector Tabs / Pills */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-800 text-xs">
                  {selectedDossier.sections?.map((sec) => (
                    <button
                      key={sec.section_number}
                      type="button"
                      onClick={() => setActiveSectionNum(sec.section_number)}
                      className={`px-3 py-1.5 rounded-lg text-[11px] font-mono whitespace-nowrap transition-colors cursor-pointer ${
                        activeSectionNum === sec.section_number
                          ? 'bg-cyan-500 text-slate-950 font-bold'
                          : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
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
                        <h3 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">
                          {s.section_number}. {s.title}
                        </h3>
                        <span className="font-mono text-[11px] text-cyan-400">
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
        <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
                Statutory Traceability Matrix
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Deterministic lineage: Requirement &rarr; Product DNA &rarr; Evidence &rarr; CAD &rarr; Assessment &rarr; Finding &rarr; Review &rarr; Attestation.
              </p>
            </div>

            <input
              type="text"
              placeholder="Filter by clause, parameter, or status..."
              value={traceFilter}
              onChange={(e) => setTraceFilter(e.target.value)}
              className="text-xs font-mono px-3 py-1.5 border border-slate-700 rounded-lg bg-slate-900 text-slate-100 placeholder-slate-500 w-full sm:w-72 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-slate-800 rounded-lg">
              <thead className="bg-slate-900/60 border-b border-slate-800 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="p-3">Requirement / Clause</th>
                  <th className="p-3">Product DNA Fact</th>
                  <th className="p-3">Supporting Evidence</th>
                  <th className="p-3">CAD Telemetry</th>
                  <th className="p-3">Assessment Result</th>
                  <th className="p-3">Review Decision</th>
                  <th className="p-3">Attestation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTraceRows.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="p-6 text-center text-slate-500 font-mono text-xs">
                      No matching traceability records found.
                    </td>
                  </tr>
                ) : (
                  filteredTraceRows.map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3 font-medium">
                        <div className="font-bold text-slate-200">{r.requirement_id}</div>
                        <div className="font-mono text-[11px] text-cyan-400">Clause {r.clause}</div>
                      </td>
                      <td className="p-3">
                        <div className="font-mono text-[11px] font-semibold text-slate-200">{r.parameter_key}</div>
                        <div className="text-[11px] text-slate-400">{r.dna_value}</div>
                      </td>
                      <td className="p-3 font-mono text-[10px]">
                        <div className="text-slate-300">ID: {r.evidence_id}</div>
                        <div className="text-slate-400">Status: <strong className="text-cyan-300">{r.evidence_acceptance}</strong></div>
                      </td>
                      <td className="p-3 font-mono text-[10px]">
                        {r.cad_measurement_id !== 'N/A' ? (
                          <>
                            <div className="text-cyan-400 font-semibold">{r.cad_measurement_value}</div>
                            <div className="text-slate-500">{r.cad_measurement_id}</div>
                          </>
                        ) : (
                          <span className="text-slate-500">N/A</span>
                        )}
                      </td>
                      <td className="p-3">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded border font-bold ${
                            r.assessment_state === 'ENGINEERING_PASS'
                              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                              : r.assessment_state === 'ENGINEERING_GAP'
                              ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                              : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                          }`}
                        >
                          {r.assessment_state}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-[11px]">
                        {r.review_decision !== 'NONE' ? (
                          <span className="font-semibold text-slate-200">{r.review_decision}</span>
                        ) : (
                          <span className="text-slate-500">NONE</span>
                        )}
                      </td>
                      <td className="p-3 font-mono text-[11px]">
                        {r.attestation_id !== 'NONE' ? (
                          <span className="text-cyan-400 font-semibold">ATT-{r.attestation_id.slice(0, 8)}</span>
                        ) : (
                          <span className="text-slate-500">NONE</span>
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
        <div className="bg-[#0f1422]/90 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
                Cryptographic Integrity Verification
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Verifies byte-level SHA-256 integrity of all dossier artifacts against database digests.
              </p>
            </div>

            <span
              className={`px-3 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 border ${
                integrityData?.is_intact
                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                  : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
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
              <div key={d.dossier_id} className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-200 font-mono">Dossier v{d.version}</span>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                      d.is_tamper_free ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60' : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                    }`}
                  >
                    {d.is_tamper_free ? 'TAMPER-FREE' : 'INVALID'}
                  </span>
                </div>
                <div className="font-mono text-[10px] text-slate-400 break-all">
                  Canonical Digest: <strong className="text-cyan-400">{d.stored_dossier_digest}</strong>
                </div>

                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">Artifacts:</div>
                  {d.artifacts_verified?.map((art) => (
                    <div key={art.artifact_id} className="text-[10px] font-mono bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200">{art.artifact_type}</span>
                        <span className={art.hash_valid ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                          {art.hash_valid ? 'HASH MATCH' : 'MISMATCH'}
                        </span>
                      </div>
                      <div className="text-slate-400 truncate mt-0.5">Stored: {art.stored_hash}</div>
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
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';
      case 'ENGINEERING_GAP':
      case 'REJECTED_PRESENT':
      case 'CONFLICT_DETECTED':
      case 'REJECTED_ITEMS':
      case 'REVOKED':
      case 'OPEN':
        return 'bg-rose-950/60 text-rose-300 border-rose-800/60';
      case 'PARTIALLY_ACCEPTED':
      case 'PARTIALLY_VERIFIED':
      case 'DATA_REQUIRED':
      case 'PENDING':
      case 'WAIVED':
      case 'NEEDS_UPDATE':
        return 'bg-amber-950/60 text-amber-300 border-amber-800/60';
      default:
        return 'bg-slate-900 text-slate-300 border-slate-800';
    }
  };

  return (
    <div className={`p-2.5 rounded-xl border flex flex-col justify-between ${getStyle(state)}`}>
      <span className="text-[10px] font-mono uppercase font-semibold opacity-75">{title}</span>
      <span className="font-mono text-xs font-bold mt-1 tracking-tight truncate">{state || 'NONE'}</span>
    </div>
  );
}

function CounterBox({ label, val, textClass = 'text-slate-200' }) {
  return (
    <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
      <div className={`text-base font-bold font-mono ${textClass}`}>{val}</div>
      <div className="text-[10px] text-slate-400 font-medium truncate mt-0.5">{label}</div>
    </div>
  );
}

function SectionContentDisplay({ sectionKey, content }) {
  if (!content) {
    return <div className="text-xs text-slate-500 font-mono">Empty section.</div>;
  }

  return (
    <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 text-xs font-mono overflow-x-auto max-h-96">
      <pre className="whitespace-pre-wrap text-[11px] text-cyan-300 leading-relaxed">
        {JSON.stringify(content, null, 2)}
      </pre>
    </div>
  );
}
