import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { sojuApiBaseUrl } from '$lib/config';

import { apiUrl, fetchWithTimeout, jsonPost } from './http';

describe('fetchWithTimeout', () => {
  let originalFetch: typeof fetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.useRealTimers();
  });

  it('rejects with a clear message when the request hangs past the timeout', async () => {
    vi.useFakeTimers();
    globalThis.fetch = vi.fn((_url, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => {
          reject(new DOMException('The operation was aborted.', 'AbortError'));
        });
      });
    }) as unknown as typeof fetch;

    const pending = fetchWithTimeout('http://example.test/slow', {}, 50);
    const expectation = expect(pending).rejects.toThrow(/timed out after 50ms/);
    await vi.advanceTimersByTimeAsync(50);
    await expectation;
  });

  it('propagates non-timeout fetch errors unchanged', async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('network down'))) as unknown as typeof fetch;

    await expect(fetchWithTimeout('http://example.test/x', {}, 1000)).rejects.toThrow('network down');
  });

  it('resolves normally when the request finishes before the timeout', async () => {
    const response = new Response('ok');
    globalThis.fetch = vi.fn(() => Promise.resolve(response)) as unknown as typeof fetch;

    await expect(fetchWithTimeout('http://example.test/fast', {}, 1000)).resolves.toBe(response);
  });
});

describe('jsonPost', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('posts JSON to apiUrl(path) with Content-Type', async () => {
    const response = new Response('{}', { status: 200 });
    const fetchMock = vi.fn().mockResolvedValue(response);
    vi.stubGlobal('fetch', fetchMock);

    await expect(jsonPost('/v1/audio/speech', { input: 'hi' })).resolves.toBe(response);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(apiUrl('/v1/audio/speech'));
    expect(url).toBe(`${sojuApiBaseUrl}/v1/audio/speech`);
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    expect(JSON.parse(String(init.body))).toEqual({ input: 'hi' });
  });
});
