import { apiClient } from './client';

export const dnaApi = {
  async getProductDNA(jobId) {
    return await apiClient.get(`/jobs/${jobId}/dna`);
  },

  async addDNAParameter(jobId, payload) {
    return await apiClient.post(`/jobs/${jobId}/dna`, payload);
  },

  async updateDNAParameter(jobId, paramId, payload) {
    return await apiClient.patch(`/jobs/${jobId}/dna/${paramId}`, payload);
  },

  async deleteDNAParameter(jobId, paramId) {
    return await apiClient.delete(`/jobs/${jobId}/dna/${paramId}`);
  },
};
