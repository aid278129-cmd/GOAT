import { apiClient } from './client';

const TOKEN_KEY = 'goat_auth_token';
const USER_KEY = 'goat_current_user';

export const authApi = {
  async bootstrap() {
    const data = await apiClient.post('/auth/bootstrap', {});
    if (data?.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    }
    return data;
  },

  async login(email, password) {
    const data = await apiClient.post('/auth/login', { email, password });
    if (data?.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    }
    return data;
  },

  async register(payload) {
    const data = await apiClient.post('/auth/register', payload);
    if (data?.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    }
    return data;
  },

  async getMe() {
    return await apiClient.get('/auth/me');
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  getCurrentUser() {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
};
