import { AI_FETCH_TIMEOUT_MS, apiUrl, fetchWithTimeout, readError } from '$lib/ai/http';
import { aiEmbedModel } from '$lib/config';

/**
 * Embed free-form text via Ollama's native `/api/embeddings` (browser → `PUBLIC_AI_BASE_URL`).
 *
 * Used to embed the Practice theme in the browser so `/api/practice/retrieve` only needs to read
 * the cache built by `soju embed-index` and compute cosine similarity (no server-side Ollama call).
 *
 * @throws {Error} If Ollama is unreachable, returns an error, or returns no embedding.
 */
export async function embedQueryText(text: string): Promise<number[]> {
  const response = await fetchWithTimeout(
    apiUrl('/api/embeddings'),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: aiEmbedModel, prompt: text })
    },
    AI_FETCH_TIMEOUT_MS
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = (await response.json()) as { embedding?: unknown };
  if (!Array.isArray(payload.embedding) || payload.embedding.length === 0) {
    throw new Error('Ollama returned an empty embedding for the theme.');
  }

  return payload.embedding as number[];
}
