import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchWithTimeout } from './http';

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
