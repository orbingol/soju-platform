import { base } from '$app/paths';

import type { PracticeRetrieveResult } from './retrieve';

/**
 * POST a browser-embedded theme vector to the dev-only `/api/practice/retrieve` endpoint.
 *
 * @throws {Error} With the endpoint's error message (e.g. missing embedding cache, dimension
 *   mismatch, unknown level) or a generic message if the response body has no `error` field.
 */
export async function fetchRetrieval(level: string, queryVector: number[], options: { includeUnassigned?: boolean } = {}): Promise<PracticeRetrieveResult> {
  const response = await fetch(`${base}/api/practice/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      level,
      queryVector,
      ...(options.includeUnassigned ? { includeUnassigned: true } : {}),
    }),
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error((body as { error?: string }).error ?? `Retrieve failed (${response.status})`);
  }
  return body as PracticeRetrieveResult;
}

export type StagingKind = 'exercises' | 'stories' | 'vocabulary';

/**
 * POST a staging document to the dev-only `/api/staging` endpoint.
 *
 * @throws {Error} With the endpoint's `error` field when present, otherwise ``Save failed``.
 */
export async function postStaging(kind: StagingKind, payload: unknown, date?: string): Promise<void> {
  const response = await fetch(`${base}/api/staging`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(date ? { kind, payload, date } : { kind, payload }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error ?? 'Save failed');
  }
}

/** Persist a practice session's staging docs (exercises required; stories/vocabulary optional). */
export async function savePracticeSessionToStaging(
  docs: {
    exercises: unknown;
    stories?: unknown;
    vocabulary?: unknown;
  },
  date: string,
): Promise<void> {
  const jobs = [postStaging('exercises', docs.exercises, date)];
  if (docs.stories) jobs.push(postStaging('stories', docs.stories, date));
  if (docs.vocabulary) jobs.push(postStaging('vocabulary', docs.vocabulary));
  await Promise.all(jobs);
}
