import React, { useState, useEffect, useCallback } from 'react';
import { reviewApi } from '../api/review';
import { assessmentApi } from '../api/assessment';

export function ReviewWorkspaceView({
  jobId,
  currentJob,
  currentUser,
  onShowToast,
  evidenceList = [],
}) {
  const [activeTab, setActiveTab] = useState('reviews');
  const [loading, setLoading] = useState(false);

  const [reviews, setReviews] = useState([]);
  const [reviewFilter, setReviewFilter] = useState('ALL');
  const [selectedReview, setSelectedReview] = useState(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [creatingReviewModal, setCreatingReviewModal] = useState(false);
  const [newReviewData, setNewReviewData] = useState({
    review_type: 'ENGINEERING_JUDGEMENT',
    title: '',
    description: '',
    priority: 'MEDIUM',
  });

  const [attestations, setAttestations] = useState([]);
  const [selectedAttestation, setSelectedAttestation] = useState(null);
  const [newAttestationModal, setNewAttestationModal] = useState(false);
  const [supersedeModal, setSupersedeModal] = useState(false);
  const [revokeModal, setRevokeModal] = useState(false);
  const [revocationReason, setRevocationReason] = useState('');
  const [latestAssessmentRun, setLatestAssessmentRun] = useState(null);
  const [attestationForm, setAttestationForm] = useState({
    attestation_type: 'STANDARDS_CONFORMANCE',
    attestation_statement: 'I hereby declare and attest that I have reviewed the engineering assessments, test reports, and Product DNA parameters for this compliance job and verify conformance to the applicable statutory standard.',
    decision: 'CONFORMANT',
    decision_rationale: '',
    conditions_or_stipulations: '',
  });

  const [findings, setFindings] = useState([]);
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [findingActionModal, setFindingActionModal] = useState(false);
  const [findingActionType, setFindingActionType] = useState('RESOLVED');
  const [findingNotes, setFindingNotes] = useState('');

  const loadReviews = useCallback(async () => {
    if (!jobId) return;
    try {
      setLoading(true);
      const res = await reviewApi.listReviews(jobId);
      setReviews(res.items || []);
    } catch (err) {
      console.warn('Failed to load review items:', err);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const loadAttestations = useCallback(async () => {
    if (!jobId) return;
    try {
      const res = await reviewApi.listAttestations(jobId);
      setAttestations(res.attestations || []);
    } catch (err) {
      console.warn('Failed to load attestations:', err);
    }
  }, [jobId]);

  const loadFindings = useCallback(async () => {
    if (!jobId) return;
    try {
      const res = await assessmentApi.listFindings(jobId);
      setFindings(res || []);
    } catch (err) {
      console.warn('Failed to load findings:', err);
    }
  }, [jobId]);

  const loadLatestRun = useCallback(async () => {
    if (!jobId) return;
    try {
      const run = await assessmentApi.getLatestAssessment(jobId);
      setLatestAssessmentRun(run);
    } catch (err) {
      setLatestAssessmentRun(null);
    }
  }, [jobId]);

  useEffect(() => {
    loadReviews();
    loadAttestations();
    loadFindings();
    loadLatestRun();
  }, [loadReviews, loadAttestations, loadFindings, loadLatestRun]);

  const handleAutoPopulate = async () => {
    if (!latestAssessmentRun?.id) {
      onShowToast?.('No assessment run found to populate reviews from. Run assessment first.');
      return;
    }
    try {
      setLoading(true);
      const res = await reviewApi.autoPopulateReviews(jobId, latestAssessmentRun.id);
      onShowToast?.(`Successfully created ${res.created_count || 0} review items from assessment findings.`);
      await loadReviews();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to auto-populate review items.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision) => {
    if (!selectedReview) return;
    if ((decision === 'REJECT' || decision === 'RETURN') && !decisionNotes.trim()) {
      onShowToast?.('Decision notes are mandatory when rejecting or returning a review item.');
      return;
    }

    try {
      setLoading(true);
      await reviewApi.submitDecision(jobId, selectedReview.id, decision, decisionNotes);
      onShowToast?.(`Review item successfully ${decision}ED.`);
      setSelectedReview(null);
      setDecisionNotes('');
      await loadReviews();
      await loadFindings();
    } catch (err) {
      onShowToast?.(err.message || `Failed to submit review decision.`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReview = async (e) => {
    e.preventDefault();
    if (!newReviewData.title.trim() || !newReviewData.description.trim()) {
      onShowToast?.('Title and description are required.');
      return;
    }
    try {
      setLoading(true);
      await reviewApi.createReview(jobId, {
        ...newReviewData,
        assessment_run_id: latestAssessmentRun?.id || null,
      });
      onShowToast?.('Review item created successfully.');
      setCreatingReviewModal(false);
      setNewReviewData({
        review_type: 'ENGINEERING_JUDGEMENT',
        title: '',
        description: '',
        priority: 'MEDIUM',
      });
      await loadReviews();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to create review item.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAttestation = async (e) => {
    e.preventDefault();
    if (!latestAssessmentRun?.id) {
      onShowToast?.('An assessment run is strictly required before issuing an attestation.');
      return;
    }
    if (!attestationForm.decision_rationale.trim()) {
      onShowToast?.('Engineering decision rationale is mandatory.');
      return;
    }

    try {
      setLoading(true);
      await reviewApi.submitAttestation(jobId, {
        assessment_run_id: latestAssessmentRun.id,
        attestation_type: attestationForm.attestation_type,
        attestation_statement: attestationForm.attestation_statement,
        decision: attestationForm.decision,
        decision_rationale: attestationForm.decision_rationale,
        conditions_or_stipulations: attestationForm.conditions_or_stipulations,
      });
      onShowToast?.('Authoritative human attestation issued and activated.');
      setNewAttestationModal(false);
      await loadAttestations();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to issue attestation.');
    } finally {
      setLoading(false);
    }
  };

  const handleSupersede = async (e) => {
    e.preventDefault();
    if (!selectedAttestation) return;
    try {
      setLoading(true);
      await reviewApi.supersedeAttestation(jobId, selectedAttestation.id, {
        attestation_statement: attestationForm.attestation_statement,
        decision: attestationForm.decision,
        decision_rationale: attestationForm.decision_rationale,
        conditions_or_stipulations: attestationForm.conditions_or_stipulations,
      });
      onShowToast?.('Attestation superseded with immutable replacement.');
      setSupersedeModal(false);
      setSelectedAttestation(null);
      await loadAttestations();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to supersede attestation.');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (e) => {
    e.preventDefault();
    if (!selectedAttestation) return;
    if (!revocationReason.trim()) {
      onShowToast?.('A substantive revocation reason is strictly mandatory.');
      return;
    }
    try {
      setLoading(true);
      await reviewApi.revokeAttestation(jobId, selectedAttestation.id, revocationReason);
      onShowToast?.('Attestation formally revoked.');
      setRevokeModal(false);
      setSelectedAttestation(null);
      setRevocationReason('');
      await loadAttestations();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to revoke attestation.');
    } finally {
      setLoading(false);
    }
  };

  const handleFindingAction = async (e) => {
    e.preventDefault();
    if (!selectedFinding) return;
    if (!findingNotes.trim()) {
      onShowToast?.(`Rationale is strictly mandatory when setting finding to ${findingActionType}.`);
      return;
    }
    try {
      setLoading(true);
      await reviewApi.reviewFinding(jobId, selectedFinding.id, findingActionType, findingNotes);
      onShowToast?.(`Finding status updated to ${findingActionType}.`);
      setFindingActionModal(false);
      setSelectedFinding(null);
      setFindingNotes('');
      await loadFindings();
    } catch (err) {
      onShowToast?.(err.message || 'Failed to update finding.');
    } finally {
      setLoading(false);
    }
  };

  const filteredReviews = reviews.filter((r) => {
    if (reviewFilter === 'ALL') return true;
    return r.status === reviewFilter;
  });

  const activeAttestation = attestations.find((a) => a.status === 'ACTIVE');

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="material-symbols-outlined text-cyan-400 text-base">rate_review</span>
            <span className="text-[10px] font-mono tracking-widest uppercase text-cyan-400 font-semibold">
              Statutory Engineering Governance
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 font-['Space_Grotesk']">
            Human Review &amp; Formal Attestation
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Separating automated inference from authoritative human decisions. 0% LLM compliance authority.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {activeTab === 'reviews' && (
            <>
              <button
                type="button"
                onClick={handleAutoPopulate}
                disabled={loading || !latestAssessmentRun}
                className="px-3 py-2 text-xs font-medium text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 rounded-lg transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-40 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm">dynamic_feed</span>
                Populate from Assessment
              </button>
              <button
                type="button"
                onClick={() => setCreatingReviewModal(true)}
                className="px-3.5 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-cyan-500/10 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm font-bold">add</span>
                New Review Item
              </button>
            </>
          )}

          {activeTab === 'attestations' && (
            <button
              type="button"
              onClick={() => {
                setAttestationForm({
                  attestation_type: 'STANDARDS_CONFORMANCE',
                  attestation_statement: 'I hereby declare and attest that I have reviewed the engineering assessments, test reports, and Product DNA parameters for this compliance job and verify conformance to the applicable statutory standard.',
                  decision: 'CONFORMANT',
                  decision_rationale: '',
                  conditions_or_stipulations: '',
                });
                setNewAttestationModal(true);
              }}
              disabled={loading || !latestAssessmentRun}
              className="px-4 py-2 text-xs font-semibold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-emerald-500/10 cursor-pointer disabled:opacity-40"
            >
              <span className="material-symbols-outlined text-sm font-bold">verified</span>
              Issue Human Attestation
            </button>
          )}
        </div>
      </div>

      {/* Statutory Governance Invariant Banner */}
      <div className="bg-[#0f1422]/90 border-l-4 border-cyan-500 p-4 rounded-r-xl border-y border-r border-slate-800/80 shadow-md">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-cyan-400 text-xl mt-0.5">gavel</span>
          <div className="text-xs text-slate-300 leading-relaxed">
            <span className="font-semibold text-slate-100 block mb-0.5 font-['Space_Grotesk']">
              Statutory Governance Invariant
            </span>
            Evidence Processing ≠ Evidence Acceptance ≠ Engineering Assessment ≠ Human Review ≠ Human Attestation ≠ BIS Certification.
            Automated assessments identify gaps and trigger review requirements, but legally conformant compliance decisions strictly require signed human action.
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          type="button"
          onClick={() => setActiveTab('reviews')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'reviews'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="material-symbols-outlined text-base">checklist</span>
          Review Queue ({reviews.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('attestations')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'attestations'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="material-symbols-outlined text-base">verified_user</span>
          Human Attestations ({attestations.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('findings')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'findings'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="material-symbols-outlined text-base">warning</span>
          Findings &amp; Waivers ({findings.length})
        </button>
      </div>

      {/* Tab: Reviews */}
      {activeTab === 'reviews' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {['ALL', 'PENDING', 'ASSIGNED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'RETURNED'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setReviewFilter(st)}
                className={`px-3 py-1 rounded-full text-xs font-mono transition-colors cursor-pointer ${
                  reviewFilter === st
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {filteredReviews.length === 0 ? (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-slate-500 mb-2">assignment_turned_in</span>
              <h3 className="text-sm font-semibold text-slate-200 font-['Space_Grotesk']">No Review Items</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                No items match the selected filter. Click Populate from Assessment to pull clauses needing review.
              </p>
            </div>
          ) : (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                      <th className="py-3 px-4">Priority</th>
                      <th className="py-3 px-4">Review Item</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Assigned To</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredReviews.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <span
                            className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold border ${
                              item.priority === 'CRITICAL'
                                ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                                : item.priority === 'HIGH'
                                ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {item.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-200">{item.title}</div>
                          <div className="text-[11px] text-slate-400 truncate max-w-md mt-0.5">
                            {item.description}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-[11px] text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                            {item.review_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {item.assigned_reviewer_email || (
                            <span className="italic text-slate-500">Unassigned</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold border ${
                              item.status === 'APPROVED'
                                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                                : item.status === 'REJECTED'
                                ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                                : item.status === 'RETURNED'
                                ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                                : item.status === 'IN_REVIEW'
                                ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {item.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedReview(item);
                              setDecisionNotes(item.decision_notes || '');
                            }}
                            className="px-2.5 py-1 text-xs font-medium text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 rounded-md transition-colors cursor-pointer"
                          >
                            Inspect &amp; Decide
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Attestations */}
      {activeTab === 'attestations' && (
        <div className="flex flex-col gap-6">
          {activeAttestation ? (
            <div className="bg-[#0f1422]/90 border border-emerald-500/40 rounded-xl p-6 shadow-xl flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 flex items-center justify-center">
                    <span className="material-symbols-outlined text-lg">verified</span>
                  </div>
                  <div>
                    <span className="text-xs font-mono uppercase tracking-wider text-emerald-400 font-bold">
                      ACTIVE STATUTORY ATTESTATION
                    </span>
                    <h3 className="text-base font-bold text-slate-100 font-['Space_Grotesk'] mt-0.5">
                      {activeAttestation.attestation_type}
                    </h3>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedAttestation(activeAttestation);
                      setAttestationForm({
                        attestation_type: activeAttestation.attestation_type,
                        attestation_statement: activeAttestation.attestation_statement,
                        decision: activeAttestation.decision,
                        decision_rationale: activeAttestation.decision_rationale,
                        conditions_or_stipulations: activeAttestation.conditions_or_stipulations || '',
                      });
                      setSupersedeModal(true);
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors flex items-center gap-1 border border-slate-700 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm">sync</span>
                    Supersede
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedAttestation(activeAttestation);
                      setRevokeModal(true);
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-rose-300 bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm">cancel</span>
                    Revoke
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Attestor Identity</span>
                  <div className="font-semibold text-slate-200 mt-1">{activeAttestation.attestor_email}</div>
                  <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60 inline-block mt-1">
                    ROLE: {activeAttestation.attestor_role}
                  </span>
                </div>

                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Decision &amp; Timestamp</span>
                  <div className="font-semibold text-slate-200 mt-1">{activeAttestation.decision}</div>
                  <div className="font-mono text-[10px] text-slate-400 mt-1">
                    {new Date(activeAttestation.attested_at).toLocaleString()}
                  </div>
                </div>

                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block text-[11px]">Cryptographic Scope</span>
                  <div className="font-semibold text-slate-200 mt-1">
                    {activeAttestation.scope?.clause_count || 0} Clauses Covered
                  </div>
                  <div className="font-mono text-[10px] text-slate-400 mt-1">
                    {activeAttestation.scope?.evidence_hashes?.length || 0} Evidence Hashes Bounded
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-800 text-xs">
                <span className="font-semibold text-slate-200 block mb-1">Declaration Statement:</span>
                <p className="text-slate-300 italic leading-relaxed">
                  "{activeAttestation.attestation_statement}"
                </p>
              </div>

              <div className="text-xs">
                <span className="font-semibold text-slate-200 block mb-1">Decision Rationale:</span>
                <p className="text-slate-400">{activeAttestation.decision_rationale}</p>
              </div>
            </div>
          ) : (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-slate-500 mb-2">shield</span>
              <h3 className="text-sm font-semibold text-slate-200 font-['Space_Grotesk']">No Active Attestation</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md">
                No formal regulatory compliance attestation has been issued for this job yet.
                An authorized Reviewer or Admin must review findings and execute an attestation.
              </p>
            </div>
          )}

          {attestations.length > 0 && (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="px-4 py-3 bg-slate-900/60 border-b border-slate-800 font-semibold text-xs text-slate-200 font-['Space_Grotesk']">
                Attestation Audit History
              </div>
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-900/40 border-b border-slate-800 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Type</th>
                    <th className="py-2.5 px-4">Attestor</th>
                    <th className="py-2.5 px-4">Decision</th>
                    <th className="py-2.5 px-4">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {attestations.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold border ${
                            a.status === 'ACTIVE'
                              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                              : a.status === 'SUPERSEDED'
                              ? 'bg-slate-800 text-slate-400 border-slate-700'
                              : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-medium text-slate-200">{a.attestation_type}</td>
                      <td className="py-2.5 px-4 text-slate-400">{a.attestor_email}</td>
                      <td className="py-2.5 px-4 font-semibold text-slate-200">{a.decision}</td>
                      <td className="py-2.5 px-4 font-mono text-[11px] text-slate-400">
                        {new Date(a.attested_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Findings */}
      {activeTab === 'findings' && (
        <div className="flex flex-col gap-4">
          {findings.length === 0 ? (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-emerald-400 mb-2">task_alt</span>
              <h3 className="text-sm font-semibold text-slate-200 font-['Space_Grotesk']">Zero Outstanding Findings</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                No statutory compliance gaps or non-conformances identified in current assessment run.
              </p>
            </div>
          ) : (
            <div className="bg-[#0f1422]/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
                      <th className="py-3 px-4">Severity</th>
                      <th className="py-3 px-4">Finding Title</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Resolution / Waiver Notes</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {findings.map((f) => (
                      <tr key={f.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <span
                            className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold border ${
                              f.severity === 'CRITICAL'
                                ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                                : f.severity === 'MAJOR'
                                ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                                : 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                            }`}
                          >
                            {f.severity}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-200">{f.title}</div>
                          <div className="text-[11px] text-slate-400 truncate max-w-md mt-0.5">
                            {f.description}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold border ${
                              f.status === 'RESOLVED'
                                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                                : f.status === 'WAIVED'
                                ? 'bg-purple-950/60 text-purple-300 border-purple-800/60'
                                : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                            }`}
                          >
                            {f.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400 text-[11px]">
                          {f.review_notes || <span className="italic text-slate-500">Pending resolution</span>}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedFinding(f);
                                setFindingActionType('RESOLVED');
                                setFindingNotes(f.review_notes || '');
                                setFindingActionModal(true);
                              }}
                              className="px-2.5 py-1 text-xs font-medium text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-800/60 rounded-md transition-colors cursor-pointer"
                            >
                              Resolve
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedFinding(f);
                                setFindingActionType('WAIVED');
                                setFindingNotes(f.review_notes || '');
                                setFindingActionModal(true);
                              }}
                              className="px-2.5 py-1 text-xs font-medium text-purple-300 bg-purple-950/60 hover:bg-purple-900/60 border border-purple-800/60 rounded-md transition-colors cursor-pointer"
                            >
                              Waive
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Selected Review Modal */}
      {selectedReview && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0d121f] rounded-2xl border border-slate-800 shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div>
                <span className="font-mono text-[10px] bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 px-2 py-0.5 rounded font-bold">
                  {selectedReview.review_type}
                </span>
                <h2 className="text-base font-bold text-slate-100 font-['Space_Grotesk'] mt-1">{selectedReview.title}</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReview(null)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex flex-col gap-4 text-xs">
              <div>
                <span className="font-semibold text-slate-200 block mb-1">Description / Context:</span>
                <p className="text-slate-400">{selectedReview.description}</p>
              </div>

              {selectedReview.review_snapshot?.requirement?.requirement_text && (
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="font-semibold text-slate-200 block mb-1">
                    Statutory Clause: {selectedReview.review_snapshot.requirement.clause_reference}
                  </span>
                  <p className="text-slate-400">
                    {selectedReview.review_snapshot.requirement.requirement_text}
                  </p>
                </div>
              )}

              {selectedReview.review_snapshot?.evidence_references?.length > 0 && (
                <div>
                  <span className="font-semibold text-slate-200 block mb-1">
                    Cryptographic Evidence Backing:
                  </span>
                  <div className="space-y-1.5">
                    {selectedReview.review_snapshot.evidence_references.map((ev, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex flex-col gap-1"
                      >
                        <div className="font-semibold text-slate-200">{ev.file_name}</div>
                        <div className="font-mono text-[10px] text-cyan-400 break-all">
                          SHA-256: {ev.sha256}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-200 block mb-1">
                  Reviewer Decision Notes / Engineering Rationale:
                  {(selectedReview.status === 'REJECTED' || selectedReview.status === 'RETURNED') && (
                    <span className="text-rose-400 font-bold ml-1">*Mandatory</span>
                  )}
                </label>
                <textarea
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  placeholder="Enter substantive regulatory review rationale..."
                  rows={3}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
                />
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
              <span className="font-mono text-[11px] text-slate-400">
                Reviewer: {currentUser?.email || 'Logged Reviewer'}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDecision('RETURN')}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs font-medium text-amber-300 bg-amber-950/60 hover:bg-amber-900/60 border border-amber-800/60 rounded-lg transition-colors cursor-pointer"
                >
                  Return for Rework
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision('REJECT')}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs font-medium text-rose-300 bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition-colors cursor-pointer"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision('APPROVE')}
                  disabled={loading}
                  className="px-4 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 rounded-lg transition-all shadow-md shadow-emerald-500/20 cursor-pointer"
                >
                  Approve
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Creating Review Modal */}
      {creatingReviewModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateReview}
            className="bg-[#0d121f] rounded-2xl border border-slate-800 shadow-2xl max-w-lg w-full p-5 flex flex-col gap-4 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">Initiate New Review Item</h2>
              <button
                type="button"
                onClick={() => setCreatingReviewModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Review Type</label>
              <select
                value={newReviewData.review_type}
                onChange={(e) => setNewReviewData({ ...newReviewData, review_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="ENGINEERING_JUDGEMENT">ENGINEERING_JUDGEMENT</option>
                <option value="EVIDENCE_REVIEW">EVIDENCE_REVIEW</option>
                <option value="DNA_CONFLICT_REVIEW">DNA_CONFLICT_REVIEW</option>
                <option value="DOCUMENT_REVIEW">DOCUMENT_REVIEW</option>
                <option value="TEXT_REVIEW">TEXT_REVIEW</option>
                <option value="GEOMETRY_REVIEW">GEOMETRY_REVIEW</option>
                <option value="FINDING_REVIEW">FINDING_REVIEW</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Priority</label>
              <select
                value={newReviewData.priority}
                onChange={(e) => setNewReviewData({ ...newReviewData, priority: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Title</label>
              <input
                type="text"
                value={newReviewData.title}
                onChange={(e) => setNewReviewData({ ...newReviewData, title: e.target.value })}
                placeholder="e.g. Creepage distance evaluation under IS 1293 Clause 4.2"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Description / Prompt for Reviewer</label>
              <textarea
                value={newReviewData.description}
                onChange={(e) => setNewReviewData({ ...newReviewData, description: e.target.value })}
                placeholder="Describe specifically what technical aspect requires human judgment..."
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setCreatingReviewModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg shadow-md shadow-cyan-500/20 cursor-pointer"
              >
                Create Review Item
              </button>
            </div>
          </form>
        </div>
      )}

      {/* New Attestation Modal */}
      {newAttestationModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateAttestation}
            className="bg-[#0d121f] rounded-2xl border border-slate-800 shadow-2xl max-w-xl w-full p-5 flex flex-col gap-4 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">Issue Authoritative Human Attestation</h2>
                <span className="text-[11px] text-slate-400">
                  Statutory declaration binding cryptographic evidence hashes and assessment results.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setNewAttestationModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Attestation Type</label>
              <select
                value={attestationForm.attestation_type}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="STANDARDS_CONFORMANCE">STANDARDS_CONFORMANCE</option>
                <option value="CLAUSE_COMPLIANCE">CLAUSE_COMPLIANCE</option>
                <option value="JOB_COMPLIANCE">JOB_COMPLIANCE</option>
                <option value="EVIDENCE_SUFFICIENCY">EVIDENCE_SUFFICIENCY</option>
                <option value="DEVIATION_APPROVAL">DEVIATION_APPROVAL</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Decision</label>
              <select
                value={attestationForm.decision}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono font-semibold"
              >
                <option value="CONFORMANT">CONFORMANT</option>
                <option value="NON_CONFORMANT">NON_CONFORMANT</option>
                <option value="CONDITIONAL_CONFORMANCE">CONDITIONAL_CONFORMANCE</option>
                <option value="WAIVER_GRANTED">WAIVER_GRANTED</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Formal Statutory Statement</label>
              <textarea
                value={attestationForm.attestation_statement}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_statement: e.target.value })}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Engineering Decision Rationale</label>
              <textarea
                value={attestationForm.decision_rationale}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision_rationale: e.target.value })}
                placeholder="Explain the technical basis and evidence examined..."
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Conditions or Stipulations (Optional)</label>
              <input
                type="text"
                value={attestationForm.conditions_or_stipulations}
                onChange={(e) => setAttestationForm({ ...attestationForm, conditions_or_stipulations: e.target.value })}
                placeholder="e.g. Valid only for production batches manufactured using copper grade C10100"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setNewAttestationModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 rounded-lg shadow-md shadow-emerald-500/20 cursor-pointer"
              >
                Sign &amp; Activate Attestation
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Supersede Modal */}
      {supersedeModal && selectedAttestation && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleSupersede}
            className="bg-[#0d121f] rounded-2xl border border-slate-800 shadow-2xl max-w-xl w-full p-5 flex flex-col gap-4 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">Supersede Attestation</h2>
                <span className="text-[11px] text-slate-400">
                  Replaces previous active attestation with immutable replacement record.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSupersedeModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">New Decision</label>
              <select
                value={attestationForm.decision}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono font-semibold"
              >
                <option value="CONFORMANT">CONFORMANT</option>
                <option value="NON_CONFORMANT">NON_CONFORMANT</option>
                <option value="CONDITIONAL_CONFORMANCE">CONDITIONAL_CONFORMANCE</option>
                <option value="WAIVER_GRANTED">WAIVER_GRANTED</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Updated Declaration Statement</label>
              <textarea
                value={attestationForm.attestation_statement}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_statement: e.target.value })}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Superseding Rationale</label>
              <textarea
                value={attestationForm.decision_rationale}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision_rationale: e.target.value })}
                placeholder="Document reason for superseding prior attestation..."
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setSupersedeModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 rounded-lg shadow-md shadow-cyan-500/20 cursor-pointer"
              >
                Confirm Supersede
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Revoke Modal */}
      {revokeModal && selectedAttestation && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleRevoke}
            className="bg-[#0d121f] rounded-2xl border border-rose-900/60 shadow-2xl max-w-md w-full p-5 flex flex-col gap-4 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-rose-400 font-['Space_Grotesk']">Revoke Human Attestation</h2>
              <button
                type="button"
                onClick={() => setRevokeModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <p className="text-slate-400 text-xs">
              Revoking an attestation invalidates regulatory signoff for this job. This action will be permanently recorded in the immutable audit ledger.
            </p>

            <div>
              <label className="font-semibold text-slate-200 block mb-1">
                Mandatory Revocation Reason:
              </label>
              <textarea
                value={revocationReason}
                onChange={(e) => setRevocationReason(e.target.value)}
                placeholder="State the statutory / engineering reason for revocation..."
                rows={3}
                className="w-full bg-slate-900 border border-rose-900/80 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500/20"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setRevokeModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-md shadow-rose-600/20 cursor-pointer"
              >
                Confirm Revocation
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Finding Action Modal */}
      {findingActionModal && selectedFinding && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleFindingAction}
            className="bg-[#0d121f] rounded-2xl border border-slate-800 shadow-2xl max-w-md w-full p-5 flex flex-col gap-4 text-xs animate-in fade-in zoom-in-95 duration-150"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-slate-100 font-['Space_Grotesk']">
                {findingActionType === 'RESOLVED' ? 'Resolve Compliance Finding' : 'Grant Statutory Waiver'}
              </h2>
              <button
                type="button"
                onClick={() => setFindingActionModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block font-mono">Finding:</span>
              <span className="font-semibold text-slate-200">{selectedFinding.title}</span>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                {findingActionType === 'RESOLVED' ? 'Resolution Verification Note / Evidence Ref:' : 'Statutory Waiver Rationale:'}
              </label>
              <textarea
                value={findingNotes}
                onChange={(e) => setFindingNotes(e.target.value)}
                placeholder={
                  findingActionType === 'RESOLVED'
                    ? 'State how the gap was remediated with evidence reference...'
                    : 'Provide formal regulatory justification for the waiver...'
                }
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setFindingActionModal(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-4 py-1.5 text-xs font-semibold text-white rounded-lg shadow-md cursor-pointer ${
                  findingActionType === 'RESOLVED'
                    ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20'
                    : 'bg-purple-600 hover:bg-purple-500 shadow-purple-600/20'
                }`}
              >
                {findingActionType === 'RESOLVED' ? 'Mark Resolved' : 'Grant Waiver'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
