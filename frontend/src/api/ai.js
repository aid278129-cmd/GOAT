import { apiClient } from './client';

/**
 * Authoritative AI Engineering Copilot & LangGraph API Client.
 * Connects directly to backend job-scoped AI endpoints.
 */
export const aiApi = {
  /**
   * Send a conversational query to the job-scoped AI assistant.
   */
  async sendMessage(jobId, message, conversationId = null) {
    const response = await apiClient.post('/ai/chat', {
      job_id: jobId,
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },

  /**
   * Check LLM provider configuration and health status.
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/ai/health');
      return response.data;
    } catch (err) {
      if (err.response?.status === 503) {
        return {
          configured: false,
          error: err.response.data?.detail?.error_code || 'AI_PROVIDER_NOT_CONFIGURED',
          message: err.response.data?.detail?.message || 'AI unavailable — configure an approved LLM provider.',
        };
      }
      throw err;
    }
  },

  /**
   * List conversations for a compliance job.
   */
  async getConversations(jobId) {
    const response = await apiClient.get(`/ai/conversations/${jobId}`);
    return response.data;
  },

  /**
   * Get message history for a conversation.
   */
  async getMessages(jobId, conversationId) {
    const response = await apiClient.get(`/ai/conversations/${jobId}/${conversationId}/messages`);
    return response.data;
  },

  /**
   * List pending AI action proposals for a job.
   */
  async getProposals(jobId) {
    const response = await apiClient.get(`/ai/proposals/${jobId}`);
    return response.data;
  },

  /**
   * Human gate: Confirm an AI action proposal.
   */
  async confirmProposal(proposalId) {
    const response = await apiClient.post(`/ai/proposals/${proposalId}/confirm`);
    return response.data;
  },

  /**
   * Human gate: Reject an AI action proposal.
   */
  async rejectProposal(proposalId, reason = null) {
    const response = await apiClient.post(`/ai/proposals/${proposalId}/reject`, {
      rejection_reason: reason,
    });
    return response.data;
  },
};
