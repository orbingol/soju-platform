import { describe, expect, it } from 'vitest';

import { normalizePracticeSession, parsePracticeJson } from './staging';

describe('staging', () => {
  it('normalizes practice JSON into staging documents', () => {
    const raw = {
      sentences: [{ hangul: '안녕하세요', english: 'Hello' }],
      questions: [{ question: 'How do you say hello?', answer: '안녕하세요' }],
      fill_in_blank: [{ sentence: '___ 하세요', blank: '안녕', answer: '안녕', english: 'Hello' }],
      story: {
        title: 'Morning',
        sentences: [
          { hangul: '아침이에요', english: 'It is morning' },
          { hangul: '학교에 가요', english: 'I go to school' },
        ],
      },
      vocabulary_candidates: [{ hangul: '학교', romanization: 'hak-gyo', english: 'school' }],
    };

    const docs = normalizePracticeSession(raw, '2026-07-08');

    expect(docs.exercises.staging).toBe(true);
    expect(docs.exercises.exercises.sentences).toHaveLength(1);
    expect(docs.stories?.story.sentences).toHaveLength(2);
    expect(docs.vocabulary?.entries).toHaveLength(1);
    expect(docs.vocabulary?.entries[0].id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it('parses fenced JSON from model output', () => {
    const parsed = parsePracticeJson('```json\n{"sentences":[]}\n```');
    expect(parsed.sentences).toEqual([]);
  });

  it('rejects malformed practice JSON', () => {
    expect(() => parsePracticeJson('{"sentences":[{"hangul":"안녕"}]}')).toThrow(/sentences\[0\]\.english/);
    expect(() => parsePracticeJson('[]')).toThrow(/root must be an object/);
  });

  it('gives a friendlier message when the JSON output looks truncated', () => {
    const truncated = '{"sentences": [{"hangul": "안녕하세요", "english": "Hello"';
    expect(() => parsePracticeJson(truncated)).toThrow(/truncated/i);
  });

  it('keeps the generic invalid-JSON message for non-truncated malformed JSON', () => {
    expect(() => parsePracticeJson('{not valid json}')).toThrow(/Invalid practice JSON/);
    expect(() => parsePracticeJson('{not valid json}')).not.toThrow(/truncated/i);
  });
});
