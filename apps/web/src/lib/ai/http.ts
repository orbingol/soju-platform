import { sojuApiBaseUrl } from '$lib/config';

/** Default timeout for AI complete/stream requests. */
export const AI_FETCH_TIMEOUT_MS = 60_000;

/** Short probe timeout used by health checks. */
export const HEALTH_FETCH_TIMEOUT_MS = 4_000;

export function apiUrl(path: string): string {
  return `${sojuApiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchWithTimeout(url: string, init: RequestInit = {}, timeoutMs = HEALTH_FETCH_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timeout = globalThis.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
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
  } catch (err) {
    if (timedOut) {
      throw new Error(`Request timed out after ${timeoutMs}ms: ${url}`);
    }
    throw err;
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

export async function jsonPost(path: string, body: unknown, timeoutMs = AI_FETCH_TIMEOUT_MS): Promise<Response> {
  return fetchWithTimeout(
    apiUrl(path),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
    timeoutMs,
  );
}

/** Browser-side probe for a reachable Soju OpenAI-compatible API. */
export async function checkServerAvailable(): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(apiUrl('/v1/models'));
    return response.ok;
  } catch {
    return false;
  }
}
