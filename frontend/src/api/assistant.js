/**
 * GOAT Phase 6: BIS Intelligent Assistant & Knowledge API Client
 * SIH Problem Statement 26107
 */

import { apiClient } from './client';

export const assistantApi = {
  // Conversational Assistant
  chat: async (message, conversationId = null, language = 'en') => {
    return apiClient.post('/assistant/chat', {
      message,
      conversation_id: conversationId,
      language,
    });
  },

  listConversations: async () => {
    return apiClient.get('/assistant/conversations');
  },

  getConversation: async (conversationId) => {
    return apiClient.get(`/assistant/conversations/${conversationId}`);
  },

  recommendStandard: async (productDescription, limit = 4) => {
    return apiClient.post('/assistant/recommend-standard', {
      product_description: productDescription,
      limit,
    });
  },

  compareStandards: async (standardA, standardB) => {
    return apiClient.post('/assistant/compare-standards', {
      standard_a: standardA,
      standard_b: standardB,
    });
  },

  explainClause: async (standardNumber, clauseNumber) => {
    return apiClient.post('/assistant/explain-clause', {
      standard_number: standardNumber,
      clause_number: clauseNumber,
    });
  },

  startWorkstationJob: async (payload) => {
    return apiClient.post('/assistant/start-workstation-job', payload);
  },

  // Authoritative Knowledge Layer
  searchKnowledge: async (q, topK = 5) => {
    const params = new URLSearchParams({ q, top_k: topK });
    return apiClient.get(`/knowledge/search?${params.toString()}`);
  },

  listStandards: async (category = null) => {
    const url = category ? `/knowledge/standards?category=${encodeURIComponent(category)}` : '/knowledge/standards';
    return apiClient.get(url);
  },

  getStandardDetails: async (standardId) => {
    return apiClient.get(`/knowledge/standards/${encodeURIComponent(standardId)}`);
  },

  listClauses: async (standardId) => {
    return apiClient.get(`/knowledge/standards/${encodeURIComponent(standardId)}/clauses`);
  },

  listSchemes: async () => {
    return apiClient.get('/knowledge/schemes');
  },

  listServices: async () => {
    return apiClient.get('/knowledge/services');
  },

  searchLaboratories: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.standard) params.append('standard', filters.standard);
    if (filters.city) params.append('city', filters.city);
    if (filters.state) params.append('state', filters.state);
    if (filters.q) params.append('q', filters.q);
    const qs = params.toString();
    return apiClient.get(`/knowledge/laboratories${qs ? `?${qs}` : ''}`);
  },

  getHallmarking: async () => {
    return apiClient.get('/knowledge/hallmarking');
  },

  getSourceProvenance: async (sourceId) => {
    return apiClient.get(`/knowledge/sources/${encodeURIComponent(sourceId)}`);
  },
};
