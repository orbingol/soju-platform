import { AI_FETCH_TIMEOUT_MS, apiUrl, fetchWithTimeout } from '$lib/ai/http';
import { applyClientConfig, type SojuClientConfigPayload } from '$lib/config';

let loadPromise: Promise<boolean> | null = null;

/**
 * Fetch ``GET /v1/soju/client-config`` once and apply model/tutor/TTS defaults.
 * Returns false when the backend is unreachable (env defaults remain in effect).
 */
export function ensureClientConfig(): Promise<boolean> {
  if (!loadPromise) {
    loadPromise = (async () => {
      try {
        const response = await fetchWithTimeout(apiUrl('/v1/soju/client-config'), { method: 'GET' }, AI_FETCH_TIMEOUT_MS);
        if (!response.ok) return false;
        const payload = (await response.json()) as SojuClientConfigPayload;
        applyClientConfig(payload);
        return true;
      } catch {
        return false;
      }
    })();
  }
  return loadPromise;
}
