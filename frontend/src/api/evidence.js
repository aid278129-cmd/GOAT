import { apiClient } from './client';

export const evidenceApi = {
  async listEvidence(jobId) {
    return await apiClient.get(`/jobs/${jobId}/evidence`);
  },

  async uploadEvidence(jobId, file, source = 'Engineering Upload') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', source);
    return await apiClient.upload(`/jobs/${jobId}/evidence/upload`, formData);
  },

  async getEvidence(jobId, evidenceId) {
    return await apiClient.get(`/jobs/${jobId}/evidence/${evidenceId}`);
  },

  async reviewEvidence(jobId, evidenceId, decision, reason = '') {
    return await apiClient.post(`/jobs/${jobId}/evidence/${evidenceId}/review`, {
      decision,
      reason,
    });
  },

  getDownloadUrl(jobId, evidenceId) {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';
    return `${baseUrl}/jobs/${jobId}/evidence/${evidenceId}/download`;
  },
};
