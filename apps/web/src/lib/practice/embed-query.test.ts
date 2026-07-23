import { afterEach, describe, expect, it, vi } from 'vitest';

import { embedQueryText } from './embed-query';

describe('embedQueryText', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('posts OpenAI-shaped embeddings and returns the first vector', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: [{ embedding: [0.1, 0.2, 0.3] }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(embedQueryText('café')).resolves.toEqual([0.1, 0.2, 0.3]);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/v1/embeddings');
    expect(JSON.parse(String(init.body))).toMatchObject({ input: 'café' });
  });
});
