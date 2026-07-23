import { afterEach, describe, expect, it, vi } from 'vitest';

import { postStaging, savePracticeSessionToStaging } from './client';

vi.mock('$app/paths', () => ({ base: '' }));

describe('practice staging client', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('postStaging posts kind/payload/date and resolves on ok', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await expect(postStaging('exercises', { items: [] }, '2026-07-22')).resolves.toBeUndefined();
    expect(JSON.parse(String(fetchMock.mock.calls[0][1].body))).toEqual({
      kind: 'exercises',
      payload: { items: [] },
      date: '2026-07-22',
    });
  });

  it('postStaging throws endpoint error message on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ error: 'disk full' }),
      }),
    );
    await expect(postStaging('vocabulary', {})).rejects.toThrow('disk full');
  });

  it('savePracticeSessionToStaging posts exercises and optional docs', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetchMock);

    await savePracticeSessionToStaging(
      {
        exercises: { e: 1 },
        stories: { s: 1 },
        vocabulary: { v: 1 },
      },
      '2026-07-22',
    );

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const bodies = fetchMock.mock.calls.map((call) => JSON.parse(String((call[1] as RequestInit).body)));
    expect(bodies).toEqual([
      { kind: 'exercises', payload: { e: 1 }, date: '2026-07-22' },
      { kind: 'stories', payload: { s: 1 }, date: '2026-07-22' },
      { kind: 'vocabulary', payload: { v: 1 } },
    ]);
  });
});
