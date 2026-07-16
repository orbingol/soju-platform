import { aiBaseUrl } from '$lib/config';

/** Default timeout for AI complete/stream requests. */
export const AI_FETCH_TIMEOUT_MS = 60_000;

/** Short probe timeout used by health checks. */
export const HEALTH_FETCH_TIMEOUT_MS = 4_000;

export function apiUrl(path: string): string {
  return `${aiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchWithTimeout(
  url: string,
  init: RequestInit = {},
  timeoutMs = HEALTH_FETCH_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  const external = init.signal;

  const onExternalAbort = () => controller.abort();
  if (external) {
    if (external.aborted) {
      globalThis.clearTimeout(timeout);
      controller.abort();
    } else {
      external.addEventListener('abort', onExternalAbort, { once: true });
    }
  }

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    globalThis.clearTimeout(timeout);
    external?.removeEventListener('abort', onExternalAbort);
  }
}

export async function readError(response: Response): Promise<string> {
  const detail = await response.text();
  if (import.meta.env.DEV && detail.trim()) {
    return `Request failed (${response.status}): ${detail}`;
  }
  return `Request failed (${response.status})`;
}

const HEALTH_CHECK_PATHS = ['/v1/models', '/api/tags'] as const;

/** Browser-side probe for a reachable OpenAI-compatible or Ollama server. */
export async function checkServerAvailable(): Promise<boolean> {
  for (const path of HEALTH_CHECK_PATHS) {
    try {
      const response = await fetchWithTimeout(apiUrl(path));
      if (response.ok) return true;
    } catch {
      // Try the next probe path.
    }
  }
  return false;
}
