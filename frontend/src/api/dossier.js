import { apiClient } from './client';

export const dossierApi = {
  async generateDossier(jobId) {
    return await apiClient.post(`/jobs/${jobId}/dossiers/generate`, {});
  },

  async listDossiers(jobId) {
    return await apiClient.get(`/jobs/${jobId}/dossiers`);
  },

  async getDossier(jobId, dossierId) {
    return await apiClient.get(`/jobs/${jobId}/dossiers/${dossierId}`);
  },

  async getPassport(jobId) {
    return await apiClient.get(`/jobs/${jobId}/passport`);
  },

  async getTraceability(jobId) {
    return await apiClient.get(`/jobs/${jobId}/traceability`);
  },

  async getIntegrity(jobId) {
    return await apiClient.get(`/jobs/${jobId}/integrity`);
  },

  getDownloadUrl(jobId, dossierId) {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';
    return `${baseUrl}/jobs/${jobId}/dossiers/${dossierId}/download`;
  },

  async downloadDossierPdf(jobId, dossierId, filename) {
    const url = this.getDownloadUrl(jobId, dossierId);
    const token = localStorage.getItem('zyntrix_auth_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`Download failed with HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || `Regulatory_Dossier_${dossierId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
