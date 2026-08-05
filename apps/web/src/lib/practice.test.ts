import { afterEach, describe, expect, it, vi } from 'vitest';

import { evaluatePracticeStory, generatePracticeSession, generateStoryTopic } from './practice';

describe('generatePracticeSession', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('posts generate options to the Soju practice API and returns JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ sentences: [{ hangul: '커피요.', english: 'Coffee.' }] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      generatePracticeSession({
        levelId: '1A',
        themeText: 'Ordering drinks at a café.',
        exerciseType: 'sentences',
        count: 3,
        includeUnassigned: true,
      }),
    ).resolves.toEqual({ sentences: [{ hangul: '커피요.', english: 'Coffee.' }] });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/v1/soju/practice/generate');
    expect(init.method).toBe('POST');
    const body = JSON.parse(String(init.body)) as Record<string, unknown>;
    expect(body).toMatchObject({
      level: '1A',
      theme_text: 'Ordering drinks at a café.',
      exercise_type: 'sentences',
      count: 3,
      include_unassigned: true,
    });
  });

  it('surfaces FastAPI detail errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'That topic is not appropriate for this education app.' }),
        text: async () => '',
      }),
    );

    await expect(
      generatePracticeSession({
        levelId: '1A',
        themeText: 'violence',
        exerciseType: 'sentences',
        count: 1,
      }),
    ).rejects.toThrow(/not appropriate/i);
  });
});

describe('evaluatePracticeStory', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('posts evaluate options to the Soju practice API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ feedback: 'Nice work — keep sentences short.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      evaluatePracticeStory({
        levelId: '1A',
        topic: 'Café morning',
        userStory: '카페에 가요.',
        modelStory: 'Morning\n카페에 가요.',
      }),
    ).resolves.toEqual({ feedback: 'Nice work — keep sentences short.' });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/v1/soju/practice/evaluate-story');
    expect(JSON.parse(String(init.body))).toMatchObject({
      level: '1A',
      topic: 'Café morning',
      user_story: '카페에 가요.',
      model_story: 'Morning\n카페에 가요.',
    });
  });
});

describe('generateStoryTopic', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('posts theme context to the story-topic API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ topic: 'What did you order at the café?' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      generateStoryTopic({
        levelId: '1A',
        themeText: 'Café',
        previousTopic: 'Old topic',
      }),
    ).resolves.toBe('What did you order at the café?');

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/v1/soju/practice/story-topic');
    expect(JSON.parse(String(init.body))).toMatchObject({
      level: '1A',
      theme_text: 'Café',
      previous_topic: 'Old topic',
    });
  });
});
