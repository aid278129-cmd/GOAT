import { apiClient } from './client';

export const reviewApi = {
  /**
   * List review items for a compliance job with optional filters.
   * @param {string} jobId
   * @param {Object} filters - { status, review_type, priority }
   * @returns {Promise<{ job_id: string, count: number, items: Array }>}
   */
  async listReviews(jobId, filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.review_type) params.append('review_type', filters.review_type);
    if (filters.priority) params.append('priority', filters.priority);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return await apiClient.get(`/jobs/${jobId}/reviews${qs}`);
  },

  /**
   * Manually create a new review item.
   * @param {string} jobId
   * @param {Object} data - { review_type, title, description, priority, assessment_run_id, requirement_id, assessment_result_id, finding_id }
   * @returns {Promise<Object>}
   */
  async createReview(jobId, data) {
    return await apiClient.post(`/jobs/${jobId}/reviews`, data);
  },

  /**
   * Auto-populate review items from assessment results requiring human review or resolution.
   * @param {string} jobId
   * @param {string} assessmentRunId
   * @returns {Promise<{ job_id: string, assessment_run_id: string, created_count: number, items: Array }>}
   */
  async autoPopulateReviews(jobId, assessmentRunId) {
    return await apiClient.post(`/jobs/${jobId}/reviews/auto-populate`, {
      assessment_run_id: assessmentRunId,
    });
  },

  /**
   * Get specific review item by ID with full captured snapshot.
   * @param {string} jobId
   * @param {string} reviewId
   * @returns {Promise<Object>}
   */
  async getReview(jobId, reviewId) {
    return await apiClient.get(`/jobs/${jobId}/reviews/${reviewId}`);
  },

  /**
   * Assign a reviewer to a review item.
   * @param {string} jobId
   * @param {string} reviewId
   * @param {string} reviewerId
   * @returns {Promise<Object>}
   */
  async assignReview(jobId, reviewId, reviewerId) {
    return await apiClient.post(`/jobs/${jobId}/reviews/${reviewId}/assign`, {
      reviewer_id: reviewerId,
    });
  },

  /**
   * Mark a review item as in review.
   * @param {string} jobId
   * @param {string} reviewId
   * @returns {Promise<Object>}
   */
  async startReview(jobId, reviewId) {
    return await apiClient.post(`/jobs/${jobId}/reviews/${reviewId}/start`, {});
  },

  /**
   * Submit formal human review decision (APPROVE, REJECT, RETURN).
   * @param {string} jobId
   * @param {string} reviewId
   * @param {string} decision - APPROVE | REJECT | RETURN
   * @param {string} decisionNotes - Mandatory for REJECT and RETURN
   * @returns {Promise<Object>}
   */
  async submitDecision(jobId, reviewId, decision, decisionNotes = '') {
    return await apiClient.post(`/jobs/${jobId}/reviews/${reviewId}/decision`, {
      decision,
      decision_notes: decisionNotes,
    });
  },

  /**
   * List human compliance attestations for a job.
   * @param {string} jobId
   * @returns {Promise<{ job_id: string, count: number, attestations: Array }>}
   */
  async listAttestations(jobId) {
    return await apiClient.get(`/jobs/${jobId}/attestations`);
  },

  /**
   * Submit a new formal human compliance attestation.
   * @param {string} jobId
   * @param {Object} data - { assessment_run_id, attestation_type, attestation_statement, decision, decision_rationale, review_id, conditions_or_stipulations, admin_override }
   * @returns {Promise<Object>}
   */
  async submitAttestation(jobId, data) {
    return await apiClient.post(`/jobs/${jobId}/attestations`, data);
  },

  /**
   * Get specific attestation details.
   * @param {string} jobId
   * @param {string} attestationId
   * @returns {Promise<Object>}
   */
  async getAttestation(jobId, attestationId) {
    return await apiClient.get(`/jobs/${jobId}/attestations/${attestationId}`);
  },

  /**
   * Supersede an existing active attestation.
   * @param {string} jobId
   * @param {string} attestationId
   * @param {Object} data - { attestation_statement, decision, decision_rationale, conditions_or_stipulations }
   * @returns {Promise<Object>}
   */
  async supersedeAttestation(jobId, attestationId, data) {
    return await apiClient.post(`/jobs/${jobId}/attestations/${attestationId}/supersede`, data);
  },

  /**
   * Revoke an active attestation.
   * @param {string} jobId
   * @param {string} attestationId
   * @param {string} revocationReason
   * @returns {Promise<Object>}
   */
  async revokeAttestation(jobId, attestationId, revocationReason) {
    return await apiClient.post(`/jobs/${jobId}/attestations/${attestationId}/revoke`, {
      revocation_reason: revocationReason,
    });
  },

  /**
   * Formally review or resolve a compliance finding.
   * @param {string} jobId
   * @param {string} findingId
   * @param {string} status - RESOLVED | WAIVED | UNDER_REVIEW
   * @param {string} reviewNotes
   * @returns {Promise<Object>}
   */
  async reviewFinding(jobId, findingId, status, reviewNotes) {
    return await apiClient.post(`/jobs/${jobId}/findings/${findingId}/review`, {
      status,
      review_notes: reviewNotes,
    });
  },
};
