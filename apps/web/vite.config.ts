import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Bind mounts on Docker Desktop (macOS/Windows) often miss native fs events.
    watch: {
      usePolling: true,
      interval: 300,
    },
    // Browser on the host must open HMR on the published port, not the container IP.
    hmr: {
      host: 'localhost',
      clientPort: 5173,
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
  },
});
