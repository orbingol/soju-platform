#!/usr/bin/env bash
# Run Prettier with an absolute plugin path so resolution works under pre-commit
# (Prettier ESM import resolves from repo-root noop.js, not the hook env).
set -euo pipefail

prettier_bin="$(command -v prettier)"
env_root="$(cd "$(dirname "$prettier_bin")/.." && pwd)"
plugin="$env_root/lib/node_modules/prettier-plugin-svelte/plugin.js"

if [[ ! -f "$plugin" ]]; then
  # Fallback: flat node_modules next to .bin (npm / Docker layout)
  alt="$(cd "$(dirname "$prettier_bin")/.." && pwd)/prettier-plugin-svelte/plugin.js"
  if [[ -f "$alt" ]]; then
    plugin="$alt"
  else
    echo "pre-commit-prettier: cannot find prettier-plugin-svelte near $prettier_bin" >&2
    exit 1
  fi
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
config="$root/apps/web/prettier.config.js"

exec prettier \
  --config "$config" \
  --plugin "$plugin" \
  --write \
  "$@"
