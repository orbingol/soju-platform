import { describe, expect, it } from 'vitest';

import { buildPracticeSystemPrompt } from './practice';

describe('practice helpers', () => {
  it('embeds vocabulary lists in the system prompt', () => {
    const prompt = buildPracticeSystemPrompt({
      words: [{ hangul: '학교', romanization: 'hak-gyo', english: 'school' }],
      verbs: [{ hangul: '가다', romanization: 'ga-da', english: 'to go' }],
    });
    expect(prompt).toContain('학교');
    expect(prompt).toContain('hak-gyo');
    expect(prompt).toContain('가다');
    expect(prompt).toContain('valid JSON');
  });
});
