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

  // -------------------------------------------------------------
  // Layer 1-9 Unified Assessment & Compliance Passport Endpoints
  // -------------------------------------------------------------

  /**
   * Creates a new assessment via Layer 1 ingestion.
   */
  async createAssessment(payload) {
    return await apiClient.post('/assessments', payload);
  },

  /**
   * Lists all assessments with summary counts.
   */
  async listAssessments() {
    return await apiClient.get('/assessments');
  },

  /**
   * Retrieves full assessment workspace by ID.
   */
  async getAssessment(assessmentId) {
    return await apiClient.get(`/assessments/${assessmentId}`);
  },

  /**
   * Compiles or retrieves the official evidence-backed compliance passport.
   */
  async getPassport(assessmentId) {
    return await apiClient.get(`/assessments/${assessmentId}/passport`);
  },

  /**
   * Resets or seeds the deterministic Golden SIH Demo Assessment.
   */
  async resetGoldenDemo() {
    return await apiClient.post('/assessments/demo/reset');
  },

  /**
   * Ingests verified evidence document / lab report snippet into assessment.
   */
  async addEvidence(assessmentId, { snippet, evidence_type = 'TEST_REPORT', authority = 'LAB_REPORT', page = null }) {
    return await apiClient.post(`/assessments/${assessmentId}/evidence`, {
      snippet,
      evidence_type,
      authority,
      page,
    });
  },

  /**
   * Answers a technical clarification attribute to resolve scope or requirements.
   */
  async answerClarification(assessmentId, attribute, value) {
    return await apiClient.post(`/assessments/${assessmentId}/clarify`, {
      attribute,
      value,
    });
  },

  /**
   * Context-aware chat with active assessment.
   */
  async chatWithAssessment(assessmentId, message) {
    return await apiClient.post(`/assessments/${assessmentId}/chat`, {
      message,
    });
  },
};

