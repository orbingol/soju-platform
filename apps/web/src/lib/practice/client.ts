import { base } from '$app/paths';

import type { PracticeRetrieveResult } from './retrieve';

/**
 * POST a browser-embedded theme vector to the dev-only `/api/practice/retrieve` endpoint.
 *
 * Mirrors the `saveToStaging` fetch pattern used for `/api/staging`.
 *
 * @throws {Error} With the endpoint's error message (e.g. missing embedding cache, dimension
 *   mismatch, unknown level) or a generic message if the response body has no `error` field.
 */
export async function fetchRetrieval(level: string, queryVector: number[]): Promise<PracticeRetrieveResult> {
  const response = await fetch(`${base}/api/practice/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ level, queryVector }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error((body as { error?: string }).error ?? `Retrieve failed (${response.status})`);
  }
  return body as PracticeRetrieveResult;
}
