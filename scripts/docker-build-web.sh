#!/usr/bin/env bash
# Build the static SvelteKit site via docker/Dockerfile.web (target: build).
# Same entry point for local use and GitHub Actions.
#
# Usage:
#   scripts/docker-build-web.sh                 # build image only
#   scripts/docker-build-web.sh ./site-app      # build + extract /app/build into ./site-app
#
# Controllable build-args (pass as env; unset → Dockerfile defaults):
#   PUBLIC_BASE_PATH PUBLIC_TTS_ENGINE PUBLIC_TTS_PIPER_BASE_URL PUBLIC_TTS_PIPER_VOICE
#   PUBLIC_AI_ENABLED PUBLIC_AI_API_MODE PUBLIC_AI_BASE_URL PUBLIC_AI_MODEL
#   PUBLIC_AI_EMBED_MODEL PUBLIC_AI_SYSTEM_PROMPT PUBLIC_AI_TUTOR_NAME
#
# Examples:
#   scripts/docker-build-web.sh
#   PUBLIC_BASE_PATH=/soju-platform scripts/docker-build-web.sh ./site-app
#   PUBLIC_TTS_ENGINE=piper scripts/docker-build-web.sh ./site-app
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMAGE_TAG="${IMAGE_TAG:-soju-web:static}"
EXTRACT_DIR="${1:-}"

build_args=(
  -f docker/Dockerfile.web
  --target build
  -t "$IMAGE_TAG"
)

# Forward any of these if set in the environment (empty string is still "set").
for var in \
  PUBLIC_BASE_PATH \
  PUBLIC_TTS_ENGINE \
  PUBLIC_TTS_PIPER_BASE_URL \
  PUBLIC_TTS_PIPER_VOICE \
  PUBLIC_AI_ENABLED \
  PUBLIC_AI_API_MODE \
  PUBLIC_AI_BASE_URL \
  PUBLIC_AI_MODEL \
  PUBLIC_AI_EMBED_MODEL \
  PUBLIC_AI_SYSTEM_PROMPT \
  PUBLIC_AI_TUTOR_NAME
do
  if [ -n "${!var+x}" ]; then
    build_args+=(--build-arg "${var}=${!var}")
  fi
done

docker build "${build_args[@]}" .

if [ -n "$EXTRACT_DIR" ]; then
  mkdir -p "$EXTRACT_DIR"
  cid="$(docker create "$IMAGE_TAG")"
  trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' EXIT
  docker cp "$cid:/app/build/." "$EXTRACT_DIR/"
  docker rm -f "$cid" >/dev/null
  trap - EXIT
  echo "Extracted static site to $EXTRACT_DIR"
fi
