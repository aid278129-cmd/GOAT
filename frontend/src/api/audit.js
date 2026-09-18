import { apiClient } from './client';

export const auditApi = {
  async getJobAuditTrail(jobId) {
    return await apiClient.get(`/audit/jobs/${jobId}`);
  },

  async getOrgAuditTrail(limit = 100) {
    return await apiClient.get(`/audit?limit=${limit}`);
  },
};
