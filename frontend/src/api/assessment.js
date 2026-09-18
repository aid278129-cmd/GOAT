import { apiClient } from './client';

export const assessmentApi = {
  /**
   * Triggers a real backend deterministic assessment evaluation.
   * @param {string} jobId
   * @param {string|null} standardId - Optional standard ID to evaluate, or all active standards if null
   * @returns {Promise<Object>} AssessmentRun result with run_id, state_counts, results, and findings
   */
  async evaluateAssessment(jobId, standardId = null) {
    return await apiClient.post(`/jobs/${jobId}/assessment/evaluate`, {
      standard_id: standardId || null,
    });
  },

  /**
   * Retrieves the latest assessment run and results for the job.
   * @param {string} jobId
   * @returns {Promise<Object>}
   */
  async getLatestAssessment(jobId) {
    return await apiClient.get(`/jobs/${jobId}/assessment/latest`);
  },

  /**
   * Lists all historical assessment runs for the job.
   * @param {string} jobId
   * @returns {Promise<Array>}
   */
  async listAssessmentRuns(jobId) {
    return await apiClient.get(`/jobs/${jobId}/assessment/runs`);
  },

  /**
   * Retrieves a specific assessment run by ID.
   * @param {string} jobId
   * @param {string} runId
   * @returns {Promise<Object>}
   */
  async getAssessmentRun(jobId, runId) {
    return await apiClient.get(`/jobs/${jobId}/assessment/runs/${runId}`);
  },

  /**
   * Lists all compliance findings for the job with optional status filter.
   * @param {string} jobId
   * @param {string|null} status - OPEN | UNDER_REVIEW | RESOLVED | WAIVED
   * @returns {Promise<Array>}
   */
  async listFindings(jobId, status = null) {
    const url = status 
      ? `/jobs/${jobId}/findings?status=${encodeURIComponent(status)}` 
      : `/jobs/${jobId}/findings`;
    return await apiClient.get(url);
  },

  /**
   * Updates finding status and human review notes.
   * Requires REVIEWER or ADMIN role.
   * @param {string} jobId
   * @param {string} findingId
   * @param {string} status - OPEN | UNDER_REVIEW | RESOLVED | WAIVED
   * @param {string} reviewNotes
   * @returns {Promise<Object>}
   */
  async updateFindingStatus(jobId, findingId, status, reviewNotes = '') {
    return await apiClient.patch(`/jobs/${jobId}/findings/${findingId}`, {
      status,
      review_notes: reviewNotes,
    });
  },
};
