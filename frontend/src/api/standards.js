import { apiClient } from './client';

export const standardsApi = {
  async listStandards(jobId) {
    return await apiClient.get(`/jobs/${jobId}/standards`);
  },

  async assignStandard(jobId, payload) {
    return await apiClient.post(`/jobs/${jobId}/standards`, payload);
  },

  async setActiveStandard(jobId, standardId) {
    return await apiClient.patch(`/jobs/${jobId}/standards/${standardId}/activate`, {});
  },

  async removeStandard(jobId, standardId) {
    return await apiClient.delete(`/jobs/${jobId}/standards/${standardId}`);
  },

  async listRequirements(jobId, standardId) {
    return await apiClient.get(`/jobs/${jobId}/standards/${standardId}/requirements`);
  },

  async addRequirement(jobId, standardId, payload) {
    return await apiClient.post(`/jobs/${jobId}/standards/${standardId}/requirements`, payload);
  },
};
