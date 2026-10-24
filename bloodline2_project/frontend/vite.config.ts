import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/scan': 'http://127.0.0.1:8000',
      '/payee-check': 'http://127.0.0.1:8000',
      '/score': 'http://127.0.0.1:8000',
      '/vendor-check': 'http://127.0.0.1:8000',
      '/predict-next-hop': 'http://127.0.0.1:8000',
      '/lineage': 'http://127.0.0.1:8000',
      '/trace-handoff': 'http://127.0.0.1:8000',
      '/case': 'http://127.0.0.1:8000',
      '/cases': 'http://127.0.0.1:8000',
      '/decision': 'http://127.0.0.1:8000',
      '/hold-request': 'http://127.0.0.1:8000',
      '/stats': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
      '/invoices': 'http://127.0.0.1:8000',
      '/mules': 'http://127.0.0.1:8000',
      '/transactions': 'http://127.0.0.1:8000',
      '/demo': 'http://127.0.0.1:8000'
    }
  }
});
