import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite config for Scaff-logic frontend
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
