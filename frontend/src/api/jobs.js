import { apiClient } from './client';

export const jobsApi = {
  async listJobs() {
    return await apiClient.get('/jobs');
  },

  async createJob(payload) {
    return await apiClient.post('/jobs', payload);
  },

  async getJob(jobId) {
    return await apiClient.get(`/jobs/${jobId}`);
  },

  async updateJob(jobId, payload) {
    return await apiClient.patch(`/jobs/${jobId}`, payload);
  },

  async deleteJob(jobId) {
    return await apiClient.delete(`/jobs/${jobId}`);
  },
};
