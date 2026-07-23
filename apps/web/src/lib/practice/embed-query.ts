import { AI_FETCH_TIMEOUT_MS, apiUrl, fetchWithTimeout, readError } from '$lib/ai/http';
import { aiEmbedModel } from '$lib/config';

/**
 * Embed free-form text via OpenAI-compatible ``/v1/embeddings`` (browser → Soju API).
 *
 * Used to embed the Practice theme in the browser so `/api/practice/retrieve` only needs to read
 * the cache built by `soju embed-index` and compute cosine similarity (no server-side Ollama call).
 *
 * @throws {Error} If the API is unreachable, returns an error, or returns no embedding.
 */
export async function embedQueryText(text: string): Promise<number[]> {
  const response = await fetchWithTimeout(
    apiUrl('/v1/embeddings'),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: aiEmbedModel, input: text }),
    },
    AI_FETCH_TIMEOUT_MS,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = (await response.json()) as {
    data?: Array<{ embedding?: unknown }>;
  };
  const embedding = payload.data?.[0]?.embedding;
  if (!Array.isArray(embedding) || embedding.length === 0) {
    throw new Error('Embeddings API returned an empty embedding for the theme.');
  }

  return embedding as number[];
}
