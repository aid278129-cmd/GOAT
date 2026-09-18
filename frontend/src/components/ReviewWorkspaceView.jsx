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
      onShowToast?.(`Auto-populated ${res.created_count} review item(s) from assessment results.`);
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
      onShowToast?.(`Decision notes are mandatory when ${decision}ing a review item.`);
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
      onShowToast?.('Revocation reason is strictly required.');
      return;
    }
    try {
      setLoading(true);
      await reviewApi.revokeAttestation(jobId, selectedAttestation.id, revocationReason);
      onShowToast?.('Attestation formally revoked.');
      setRevokeModal(false);
      setRevocationReason('');
      setSelectedAttestation(null);
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
    <div className="w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#1D4ED8] text-2xl">rate_review</span>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0F172A]">
              Human Review & Formal Attestation
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-[#64748B] mt-1">
            Statutory engineering governance: separating automated inference from authoritative human decisions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'reviews' && (
            <>
              <button
                type="button"
                onClick={handleAutoPopulate}
                disabled={loading || !latestAssessmentRun}
                className="px-3 py-1.5 text-xs font-medium text-[#1D4ED8] bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-sm">dynamic_feed</span>
                Populate from Assessment
              </button>
              <button
                type="button"
                onClick={() => setCreatingReviewModal(true)}
                className="px-3 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <span className="material-symbols-outlined text-sm">add</span>
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
              className="px-3.5 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-sm">verified</span>
              Issue Human Attestation
            </button>
          )}
        </div>
      </div>

      <div className="bg-[#F8FAFC] border-l-4 border-[#1D4ED8] p-4 rounded-r-lg shadow-sm">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-[#1D4ED8] text-xl mt-0.5">gavel</span>
          <div className="text-xs text-[#334155] leading-relaxed">
            <span className="font-semibold text-[#0F172A] block mb-0.5">Statutory Governance Invariant</span>
            Evidence Processing ≠ Evidence Acceptance ≠ Engineering Assessment ≠ Human Review ≠ Human Attestation ≠ BIS Certification.
            Automated assessments identify gaps and trigger review requirements, but legally conformant compliance decisions strictly require signed human action.
          </div>
        </div>
      </div>

      <div className="flex border-b border-[#E2E8F0] gap-4">
        <button
          type="button"
          onClick={() => setActiveTab('reviews')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'reviews'
              ? 'border-[#1D4ED8] text-[#1D4ED8]'
              : 'border-transparent text-[#64748B] hover:text-[#0F172A]'
          }`}
        >
          <span className="material-symbols-outlined text-base">checklist</span>
          Review Queue ({reviews.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('attestations')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'attestations'
              ? 'border-[#1D4ED8] text-[#1D4ED8]'
              : 'border-transparent text-[#64748B] hover:text-[#0F172A]'
          }`}
        >
          <span className="material-symbols-outlined text-base">verified_user</span>
          Human Attestations ({attestations.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('findings')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'findings'
              ? 'border-[#1D4ED8] text-[#1D4ED8]'
              : 'border-transparent text-[#64748B] hover:text-[#0F172A]'
          }`}
        >
          <span className="material-symbols-outlined text-base">warning</span>
          Findings & Waivers ({findings.length})
        </button>
      </div>

      {activeTab === 'reviews' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {['ALL', 'PENDING', 'ASSIGNED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'RETURNED'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setReviewFilter(st)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  reviewFilter === st
                    ? 'bg-[#1D4ED8] text-white'
                    : 'bg-[#F1F5F9] text-[#64748B] hover:bg-[#E2E8F0]'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {filteredReviews.length === 0 ? (
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-[#94A3B8] mb-2">assignment_turned_in</span>
              <h3 className="text-sm font-semibold text-[#0F172A]">No Review Items</h3>
              <p className="text-xs text-[#64748B] mt-1 max-w-sm">
                No items match the selected filter. Click Populate from Assessment to pull clauses needing review.
              </p>
            </div>
          ) : (
            <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Review Item</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Assigned To</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {filteredReviews.map((item) => (
                    <tr key={item.id} className="hover:bg-[#F8FAFC] transition-colors">
                      <td className="py-3 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold ${
                            item.priority === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-700'
                              : item.priority === 'HIGH'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {item.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#0F172A]">{item.title}</div>
                        <div className="text-[11px] text-[#64748B] truncate max-w-md mt-0.5">
                          {item.description}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-[11px] text-[#475569] bg-[#F1F5F9] px-2 py-0.5 rounded border border-[#E2E8F0]">
                          {item.review_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[#475569]">
                        {item.assigned_reviewer_email || (
                          <span className="italic text-[#94A3B8]">Unassigned</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold ${
                            item.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : item.status === 'REJECTED'
                              ? 'bg-rose-100 text-rose-800'
                              : item.status === 'RETURNED'
                              ? 'bg-amber-100 text-amber-800'
                              : item.status === 'IN_REVIEW'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-slate-100 text-slate-700'
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
                          className="px-2.5 py-1 text-xs font-medium text-[#1D4ED8] bg-blue-50 hover:bg-blue-100 rounded transition-colors"
                        >
                          Inspect & Decide
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'attestations' && (
        <div className="flex flex-col gap-6">
          {activeAttestation ? (
            <div className="bg-white border-2 border-emerald-500 rounded-lg p-6 shadow-sm flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2E8F0] pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <span className="material-symbols-outlined text-lg">verified</span>
                  </div>
                  <div>
                    <span className="text-xs font-mono uppercase tracking-wider text-emerald-700 font-bold">
                      ACTIVE STATUTORY ATTESTATION
                    </span>
                    <h3 className="text-base font-bold text-[#0F172A] mt-0.5">
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
                    className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors flex items-center gap-1"
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
                    className="px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded transition-colors flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm">cancel</span>
                    Revoke
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="bg-[#F8FAFC] p-3 rounded border border-[#E2E8F0]">
                  <span className="text-[#64748B] block text-[11px]">Attestor Identity</span>
                  <div className="font-semibold text-[#0F172A] mt-1">{activeAttestation.attestor_email}</div>
                  <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 inline-block mt-1">
                    ROLE: {activeAttestation.attestor_role}
                  </span>
                </div>

                <div className="bg-[#F8FAFC] p-3 rounded border border-[#E2E8F0]">
                  <span className="text-[#64748B] block text-[11px]">Decision & Timestamp</span>
                  <div className="font-semibold text-[#0F172A] mt-1">{activeAttestation.decision}</div>
                  <div className="font-mono text-[10px] text-[#64748B] mt-1">
                    {new Date(activeAttestation.attested_at).toLocaleString()}
                  </div>
                </div>

                <div className="bg-[#F8FAFC] p-3 rounded border border-[#E2E8F0]">
                  <span className="text-[#64748B] block text-[11px]">Cryptographic Scope</span>
                  <div className="font-semibold text-[#0F172A] mt-1">
                    {activeAttestation.scope?.clause_count || 0} Clauses Covered
                  </div>
                  <div className="font-mono text-[10px] text-[#64748B] mt-1">
                    {activeAttestation.scope?.evidence_hashes?.length || 0} Evidence Hashes Bounded
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded border border-slate-200 text-xs">
                <span className="font-semibold text-[#0F172A] block mb-1">Declaration Statement:</span>
                <p className="text-[#334155] italic leading-relaxed">
                  "{activeAttestation.attestation_statement}"
                </p>
              </div>

              <div className="text-xs">
                <span className="font-semibold text-[#0F172A] block mb-1">Decision Rationale:</span>
                <p className="text-[#475569]">{activeAttestation.decision_rationale}</p>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-[#94A3B8] mb-2">shield</span>
              <h3 className="text-sm font-semibold text-[#0F172A]">No Active Attestation</h3>
              <p className="text-xs text-[#64748B] mt-1 max-w-md">
                No formal regulatory compliance attestation has been issued for this job yet.
                An authorized Reviewer or Admin must review findings and execute an attestation.
              </p>
            </div>
          )}

          {attestations.length > 0 && (
            <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
              <div className="px-4 py-3 bg-[#F8FAFC] border-b border-[#E2E8F0] font-semibold text-xs text-[#0F172A]">
                Attestation Audit History
              </div>
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Type</th>
                    <th className="py-2.5 px-4">Attestor</th>
                    <th className="py-2.5 px-4">Decision</th>
                    <th className="py-2.5 px-4">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {attestations.map((a) => (
                    <tr key={a.id} className="hover:bg-[#F8FAFC]">
                      <td className="py-2.5 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold ${
                            a.status === 'ACTIVE'
                              ? 'bg-emerald-100 text-emerald-800'
                              : a.status === 'SUPERSEDED'
                              ? 'bg-slate-100 text-slate-700'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-medium text-[#0F172A]">{a.attestation_type}</td>
                      <td className="py-2.5 px-4 text-[#475569]">{a.attestor_email}</td>
                      <td className="py-2.5 px-4 font-semibold text-[#0F172A]">{a.decision}</td>
                      <td className="py-2.5 px-4 font-mono text-[11px] text-[#64748B]">
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

      {activeTab === 'findings' && (
        <div className="flex flex-col gap-4">
          {findings.length === 0 ? (
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-12 text-center flex flex-col items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-emerald-500 mb-2">task_alt</span>
              <h3 className="text-sm font-semibold text-[#0F172A]">Zero Outstanding Findings</h3>
              <p className="text-xs text-[#64748B] mt-1 max-w-sm">
                No statutory compliance gaps or non-conformances identified in current assessment run.
              </p>
            </div>
          ) : (
            <div className="bg-white border border-[#E2E8F0] rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#F8FAFC] border-b border-[#E2E8F0] text-[#64748B] font-semibold">
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Finding Title</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Resolution / Waiver Notes</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {findings.map((f) => (
                    <tr key={f.id} className="hover:bg-[#F8FAFC]">
                      <td className="py-3 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold ${
                            f.severity === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-700'
                              : f.severity === 'MAJOR'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {f.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#0F172A]">{f.title}</div>
                        <div className="text-[11px] text-[#64748B] truncate max-w-md mt-0.5">
                          {f.description}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded font-semibold ${
                            f.status === 'RESOLVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : f.status === 'WAIVED'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {f.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[#475569] text-[11px]">
                        {f.review_notes || <span className="italic text-[#94A3B8]">Pending resolution</span>}
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
                            className="px-2 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition-colors"
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
                            className="px-2 py-1 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded transition-colors"
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
          )}
        </div>
      )}

      {selectedReview && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="p-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8FAFC]">
              <div>
                <span className="font-mono text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">
                  {selectedReview.review_type}
                </span>
                <h2 className="text-base font-bold text-[#0F172A] mt-1">{selectedReview.title}</h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReview(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="p-4 overflow-y-auto flex flex-col gap-4 text-xs">
              <div>
                <span className="font-semibold text-[#0F172A] block mb-1">Description / Context:</span>
                <p className="text-[#475569]">{selectedReview.description}</p>
              </div>

              {selectedReview.review_snapshot?.requirement?.requirement_text && (
                <div className="bg-[#F8FAFC] p-3 rounded border border-[#E2E8F0]">
                  <span className="font-semibold text-[#0F172A] block mb-1">
                    Statutory Clause: {selectedReview.review_snapshot.requirement.clause_reference}
                  </span>
                  <p className="text-[#475569]">
                    {selectedReview.review_snapshot.requirement.requirement_text}
                  </p>
                </div>
              )}

              {selectedReview.review_snapshot?.evidence_references?.length > 0 && (
                <div>
                  <span className="font-semibold text-[#0F172A] block mb-1">
                    Cryptographic Evidence Backing:
                  </span>
                  <div className="space-y-1.5">
                    {selectedReview.review_snapshot.evidence_references.map((ev, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-50 p-2.5 rounded border border-slate-200 flex flex-col gap-1"
                      >
                        <div className="font-semibold text-[#0F172A]">{ev.file_name}</div>
                        <div className="font-mono text-[10px] text-[#64748B] break-all">
                          SHA-256: {ev.sha256}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <label className="font-semibold text-[#0F172A] block mb-1">
                  Reviewer Decision Notes / Engineering Rationale:
                  {(selectedReview.status === 'REJECTED' || selectedReview.status === 'RETURNED') && (
                    <span className="text-rose-600 font-bold ml-1">*Mandatory</span>
                  )}
                </label>
                <textarea
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  placeholder="Enter substantive regulatory review rationale..."
                  rows={3}
                  className="w-full border border-[#CBD5E1] rounded p-2 text-xs focus:ring-1 focus:ring-[#1D4ED8]"
                />
              </div>
            </div>

            <div className="p-4 border-t border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between">
              <span className="font-mono text-[11px] text-[#64748B]">
                Reviewer: {currentUser?.email || 'Logged Reviewer'}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDecision('RETURN')}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded transition-colors"
                >
                  Return for Rework
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision('REJECT')}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded transition-colors"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision('APPROVE')}
                  disabled={loading}
                  className="px-3.5 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded transition-colors"
                >
                  Approve
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {creatingReviewModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateReview}
            className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-lg w-full p-5 flex flex-col gap-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <h2 className="text-sm font-bold text-[#0F172A]">Initiate New Review Item</h2>
              <button
                type="button"
                onClick={() => setCreatingReviewModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Review Type</label>
              <select
                value={newReviewData.review_type}
                onChange={(e) => setNewReviewData({ ...newReviewData, review_type: e.target.value })}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
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
              <label className="font-semibold text-[#0F172A] block mb-1">Priority</label>
              <select
                value={newReviewData.priority}
                onChange={(e) => setNewReviewData({ ...newReviewData, priority: e.target.value })}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Title</label>
              <input
                type="text"
                value={newReviewData.title}
                onChange={(e) => setNewReviewData({ ...newReviewData, title: e.target.value })}
                placeholder="e.g. Creepage distance evaluation under IS 1293 Clause 4.2"
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Description / Prompt for Reviewer</label>
              <textarea
                value={newReviewData.description}
                onChange={(e) => setNewReviewData({ ...newReviewData, description: e.target.value })}
                placeholder="Describe specifically what technical aspect requires human judgment..."
                rows={3}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                type="button"
                onClick={() => setCreatingReviewModal(false)}
                className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded shadow-sm"
              >
                Create Review Item
              </button>
            </div>
          </form>
        </div>
      )}

      {newAttestationModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleCreateAttestation}
            className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-xl w-full p-5 flex flex-col gap-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div>
                <h2 className="text-sm font-bold text-[#0F172A]">Issue Authoritative Human Attestation</h2>
                <span className="text-[11px] text-[#64748B]">
                  Statutory declaration binding cryptographic evidence hashes and assessment results.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setNewAttestationModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Attestation Type</label>
              <select
                value={attestationForm.attestation_type}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_type: e.target.value })}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
              >
                <option value="STANDARDS_CONFORMANCE">STANDARDS_CONFORMANCE</option>
                <option value="CLAUSE_COMPLIANCE">CLAUSE_COMPLIANCE</option>
                <option value="JOB_COMPLIANCE">JOB_COMPLIANCE</option>
                <option value="EVIDENCE_SUFFICIENCY">EVIDENCE_SUFFICIENCY</option>
                <option value="DEVIATION_APPROVAL">DEVIATION_APPROVAL</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Decision</label>
              <select
                value={attestationForm.decision}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision: e.target.value })}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs font-semibold"
              >
                <option value="CONFORMANT">CONFORMANT</option>
                <option value="NON_CONFORMANT">NON_CONFORMANT</option>
                <option value="CONDITIONAL_CONFORMANCE">CONDITIONAL_CONFORMANCE</option>
                <option value="WAIVER_GRANTED">WAIVER_GRANTED</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Formal Statutory Statement</label>
              <textarea
                value={attestationForm.attestation_statement}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_statement: e.target.value })}
                rows={3}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Engineering Decision Rationale</label>
              <textarea
                value={attestationForm.decision_rationale}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision_rationale: e.target.value })}
                placeholder="Explain the technical basis and evidence examined..."
                rows={3}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Conditions or Stipulations (Optional)</label>
              <input
                type="text"
                value={attestationForm.conditions_or_stipulations}
                onChange={(e) => setAttestationForm({ ...attestationForm, conditions_or_stipulations: e.target.value })}
                placeholder="e.g. Valid only for production batches manufactured using copper grade C10100"
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                type="button"
                onClick={() => setNewAttestationModal(false)}
                className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded shadow-sm"
              >
                Sign & Activate Attestation
              </button>
            </div>
          </form>
        </div>
      )}

      {supersedeModal && selectedAttestation && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleSupersede}
            className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-xl w-full p-5 flex flex-col gap-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div>
                <h2 className="text-sm font-bold text-[#0F172A]">Supersede Attestation</h2>
                <span className="text-[11px] text-[#64748B]">
                  Replaces previous active attestation with immutable replacement record.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSupersedeModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">New Decision</label>
              <select
                value={attestationForm.decision}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision: e.target.value })}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs font-semibold"
              >
                <option value="CONFORMANT">CONFORMANT</option>
                <option value="NON_CONFORMANT">NON_CONFORMANT</option>
                <option value="CONDITIONAL_CONFORMANCE">CONDITIONAL_CONFORMANCE</option>
                <option value="WAIVER_GRANTED">WAIVER_GRANTED</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Updated Declaration Statement</label>
              <textarea
                value={attestationForm.attestation_statement}
                onChange={(e) => setAttestationForm({ ...attestationForm, attestation_statement: e.target.value })}
                rows={3}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">Superseding Rationale</label>
              <textarea
                value={attestationForm.decision_rationale}
                onChange={(e) => setAttestationForm({ ...attestationForm, decision_rationale: e.target.value })}
                placeholder="Document reason for superseding prior attestation..."
                rows={3}
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                type="button"
                onClick={() => setSupersedeModal(false)}
                className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-medium text-white bg-[#1D4ED8] hover:bg-[#1E40AF] rounded shadow-sm"
              >
                Confirm Supersede
              </button>
            </div>
          </form>
        </div>
      )}

      {revokeModal && selectedAttestation && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleRevoke}
            className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-md w-full p-5 flex flex-col gap-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <h2 className="text-sm font-bold text-rose-700">Revoke Human Attestation</h2>
              <button
                type="button"
                onClick={() => setRevokeModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <p className="text-[#64748B] text-xs">
              Revoking an attestation invalidates regulatory signoff for this job. This action will be permanently recorded in the immutable audit ledger.
            </p>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">
                Mandatory Revocation Reason:
              </label>
              <textarea
                value={revocationReason}
                onChange={(e) => setRevocationReason(e.target.value)}
                placeholder="State the statutory / engineering reason for revocation..."
                rows={3}
                className="w-full border border-rose-300 rounded p-2 text-xs focus:ring-1 focus:ring-rose-500"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                type="button"
                onClick={() => setRevokeModal(false)}
                className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 text-xs font-medium text-white bg-rose-600 hover:bg-rose-700 rounded shadow-sm"
              >
                Confirm Revocation
              </button>
            </div>
          </form>
        </div>
      )}

      {findingActionModal && selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleFindingAction}
            className="bg-white rounded-lg border border-[#E2E8F0] shadow-xl max-w-md w-full p-5 flex flex-col gap-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <h2 className="text-sm font-bold text-[#0F172A]">
                {findingActionType === 'RESOLVED' ? 'Resolve Compliance Finding' : 'Grant Statutory Waiver'}
              </h2>
              <button
                type="button"
                onClick={() => setFindingActionModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div>
              <span className="text-[11px] text-[#64748B] block">Finding:</span>
              <span className="font-semibold text-[#0F172A]">{selectedFinding.title}</span>
            </div>

            <div>
              <label className="font-semibold text-[#0F172A] block mb-1">
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
                className="w-full border border-[#CBD5E1] rounded p-2 text-xs"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
              <button
                type="button"
                onClick={() => setFindingActionModal(false)}
                className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-4 py-1.5 text-xs font-medium text-white rounded shadow-sm ${
                  findingActionType === 'RESOLVED'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-purple-600 hover:bg-purple-700'
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
