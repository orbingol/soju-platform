/** @type {import('prettier').Config} */
const config = {
  printWidth: 180,
  singleQuote: true,
  // Load prettier-plugin-svelte via CLI (`--plugin`) so pre-commit's isolated
  // node_modules can resolve it (config `plugins: [...]` resolves from repo root).
  overrides: [
    {
      files: '*.svelte',
      options: {
        parser: 'svelte',
      },
    },
  ],
};

export default config;
