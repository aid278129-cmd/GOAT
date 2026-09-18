import { apiClient } from './client';

/**
 * Authoritative CAD Intelligence API client.
 * Connects directly to backend CAD processing, measurements, and snapshot services.
 */
export const cadApi = {
  /**
   * Upload a CAD file (.stp, .step) for durable ingestion and server-side processing.
   */
  async uploadCAD(jobId, file, autoProcess = true) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_process', autoProcess);

    const response = await apiClient.post(`/jobs/${jobId}/cad/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * List all CAD models ingested for a compliance job.
   */
  async getCADModels(jobId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad`);
    return response.data;
  },

  /**
   * Get full CAD model details and statistics.
   */
  async getCADModel(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}`);
    return response.data;
  },

  /**
   * Quick status polling for a CAD model.
   */
  async getCADStatus(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/status`);
    return response.data;
  },

  /**
   * Get component assembly tree for a CAD model.
   */
  async getCADComponents(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/components`);
    return response.data;
  },

  /**
   * Get deterministic measurements established for a CAD model.
   */
  async getCADMeasurements(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/measurements`);
    return response.data;
  },

  /**
   * Get immutable CAD snapshot.
   */
  async getCADSnapshot(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/snapshot`);
    return response.data;
  },

  /**
   * Get authoritative statutory trace for a specific CAD measurement.
   */
  async getCADTrace(jobId, cadModelId, measurementId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/trace/${measurementId}`);
    return response.data;
  },

  /**
   * Map authoritative CAD measurements to Product DNA (requires ACCEPTED evidence).
   */
  async mapCADToDNA(jobId, cadModelId) {
    const response = await apiClient.post(`/jobs/${jobId}/cad/${cadModelId}/map-to-dna`);
    return response.data;
  },

  /**
   * Get lightweight visual mesh representation for Babylon.js rendering.
   */
  async getCADMesh(jobId, cadModelId) {
    const response = await apiClient.get(`/jobs/${jobId}/cad/${cadModelId}/mesh`);
    return response.data;
  },

  /**
   * Get supported CAD format capability registry.
   */
  async getCapabilities(jobId = 'default') {
    const response = await apiClient.get(`/jobs/${jobId}/cad/capabilities`);
    return response.data;
  },
};

export default cadApi;
