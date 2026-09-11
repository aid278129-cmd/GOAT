import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dynamically target backend from environment or fallback to localhost:8000
const backendTarget = process.env.VITE_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/health': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});
