import { aiBaseUrl } from '$lib/config';

export function apiUrl(path: string): string {
  return `${aiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function fetchWithTimeout(url: string, init: RequestInit = {}, timeoutMs = 4000): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function readError(response: Response): Promise<string> {
  const detail = await response.text();
  return `Request failed (${response.status}): ${detail}`;
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
