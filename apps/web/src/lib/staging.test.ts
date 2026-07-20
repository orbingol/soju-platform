import { describe, expect, it } from 'vitest';

import { normalizeFillBlankPrompt, normalizePracticeSession, parsePracticeJson } from './staging';

describe('staging', () => {
  it('normalizes practice JSON into staging documents', () => {
    const raw = {
      sentences: [{ hangul: '안녕하세요', english: 'Hello' }],
      questions: [{ prompt: 'How do you say hello?', answer: '안녕하세요', english: 'Hello' }],
      fill_in_blank: [{ prompt: 'A: 뭐 드실래요?\nB: ___ 주세요', answer: '커피', english: 'Coffee please' }],
      story: {
        title: 'Morning',
        sentences: [
          { hangul: '아침이에요', english: 'It is morning' },
          { hangul: '학교에 가요', english: 'I go to school' },
        ],
      },
      vocabulary_candidates: [{ hangul: '학교', english: 'school' }],
    };

    const docs = normalizePracticeSession(raw, '2026-07-08');

    expect(docs.exercises.staging).toBe(true);
    expect(docs.exercises.exercises.sentences).toHaveLength(1);
    expect(docs.stories?.story.sentences).toHaveLength(2);
    expect(docs.vocabulary?.entries).toHaveLength(1);
    expect(docs.vocabulary?.entries[0]).toMatchObject({ hangul: '학교', english: 'school' });
    expect(docs.vocabulary?.entries[0]).not.toHaveProperty('romanization');
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

  it('rejects an empty model body with a clear message', () => {
    expect(() => parsePracticeJson('')).toThrow(/empty body/i);
    expect(() => parsePracticeJson('   ')).toThrow(/empty body/i);
  });

  it('parses JSON from an unclosed markdown fence', () => {
    const parsed = parsePracticeJson('```json\n{"sentences":[]}\n');
    expect(parsed.sentences).toEqual([]);
  });

  it('parses questions and fill-in-blank with prompt/answer shapes', () => {
    const parsed = parsePracticeJson(
      JSON.stringify({
        questions: [{ prompt: 'A: 뭐 드릴까요?\nB: …', answer: '커피 주세요', english: 'Coffee please' }],
        fill_in_blank: [{ prompt: '커피 ___ 주세요', answer: '한 잔', english: 'one cup' }],
      }),
    );
    expect(parsed.questions).toEqual([
      { prompt: 'A: 뭐 드릴까요?\nB: …', answer: '커피 주세요', english: 'Coffee please' },
    ]);
    expect(parsed.fill_in_blank).toEqual([{ prompt: '커피 ___ 주세요', answer: '한 잔', english: 'one cup' }]);
  });

  it('rejects questions and fill-in-blank missing prompt', () => {
    expect(() => parsePracticeJson(JSON.stringify({ questions: [{ answer: '네' }] }))).toThrow(/questions\[0\]\.prompt/);
    expect(() => parsePracticeJson(JSON.stringify({ fill_in_blank: [{ answer: '커피' }] }))).toThrow(
      /fill_in_blank\[0\]\.prompt/,
    );
  });

  it('ignores romanization on practice sentences and vocabulary candidates', () => {
    const parsed = parsePracticeJson(
      JSON.stringify({
        sentences: [{ hangul: '커피 주세요', romanization: 'keopi juseyo', english: 'Please give me coffee' }],
        vocabulary_candidates: [{ hangul: '메뉴', romanization: 'me-nyu', english: 'menu' }],
      }),
    );
    expect(parsed.sentences).toEqual([{ hangul: '커피 주세요', english: 'Please give me coffee' }]);
    expect(parsed.vocabulary_candidates).toEqual([{ hangul: '메뉴', english: 'menu' }]);
  });

  it('coerces story sentences that are bare hangul strings', () => {
    const parsed = parsePracticeJson(
      JSON.stringify({
        story: {
          title: 'Weekend',
          sentences: ['지난 주말에 집에 있었어요.', 'TV를 봤어요.'],
        },
      }),
    );
    expect(parsed.story?.sentences).toEqual([
      { hangul: '지난 주말에 집에 있었어요.', english: '' },
      { hangul: 'TV를 봤어요.', english: '' },
    ]);
  });

  it('splits a story paragraph string into sentences', () => {
    const parsed = parsePracticeJson(
      JSON.stringify({
        story: {
          sentences: '집에 있었어요. TV를 봤어요.',
        },
      }),
    );
    expect(parsed.story?.sentences.map((s) => s.hangul)).toEqual(['집에 있었어요.', 'TV를 봤어요.']);
  });

  it('normalizes fill-in-blank prompts so a ___ blank is always present', () => {
    expect(normalizeFillBlankPrompt('카페에서 커피 주세요', '커피')).toBe('카페에서 ___ 주세요');
    expect(normalizeFillBlankPrompt('카페에서 ______ 주세요', '커피')).toBe('카페에서 ___ 주세요');
    expect(normalizeFillBlankPrompt('카페에서 ___ 주세요', '커피')).toBe('카페에서 ___ 주세요');

    const parsed = parsePracticeJson(
      JSON.stringify({
        fill_in_blank: [{ prompt: '친구하고 영화를 봐요', answer: '영화를', english: 'I watch a movie with a friend' }],
      }),
    );
    expect(parsed.fill_in_blank?.[0]?.prompt).toContain('___');
    expect(parsed.fill_in_blank?.[0]?.prompt).not.toContain('영화를');
  });
});
