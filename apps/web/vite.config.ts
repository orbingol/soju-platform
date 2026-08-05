import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 14321,
    // Bind mounts on Docker Desktop (macOS/Windows) often miss native fs events.
    watch: {
      usePolling: true,
      interval: 300,
    },
    // Dev publishes :14321; prod reaches Vite through nginx :8080 (VITE_HMR_CLIENT_PORT).
    hmr: {
      host: 'localhost',
      clientPort: Number(process.env.VITE_HMR_CLIENT_PORT || 14321),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
});
