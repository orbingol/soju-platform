import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const base = process.env.PUBLIC_BASE_PATH ?? '';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      // GitHub Pages serves 404.html for missing paths (SPA fallback).
      fallback: '404.html',
    }),
    paths: {
      base,
    },
    prerender: {
      entries: ['*'],
    },
  },
};

export default config;
