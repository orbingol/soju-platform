import { describe, expect, it } from 'vitest';

import { buildPracticeSystemPrompt, type PracticeGenerateOptions } from './practice';

const baseOptions: PracticeGenerateOptions = {
  level: {
    label: 'Korean 1A',
    guidance: 'Target learner: first-semester beginner.',
    grammarSummary: 'Core grammar for this level: particles, 있어요/없어요, casual_polite endings.',
  },
  themeText: 'Ordering drinks and food at a café.',
  exerciseType: 'sentences',
  count: 5,
  hangul: ['카페', '커피', '주문하다'],
  grammar: [{ id: 'hago', form: '-하고', english: 'and / with', summary: 'Connect nouns with "and".' }],
};

describe('buildPracticeSystemPrompt', () => {
  it('includes the level label, guidance, and grammar summary', () => {
    const prompt = buildPracticeSystemPrompt(baseOptions);
    expect(prompt).toContain('Korean 1A');
    expect(prompt).toContain('Target learner: first-semester beginner.');
    expect(prompt).toContain('Core grammar for this level');
  });

  it('includes the theme text', () => {
    const prompt = buildPracticeSystemPrompt(baseOptions);
    expect(prompt).toContain('Ordering drinks and food at a café.');
  });

  it('includes retrieved hangul', () => {
    const prompt = buildPracticeSystemPrompt(baseOptions);
    expect(prompt).toContain('카페');
    expect(prompt).toContain('커피');
    expect(prompt).toContain('주문하다');
  });

  it('includes retrieved grammar form, english, and summary', () => {
    const prompt = buildPracticeSystemPrompt(baseOptions);
    expect(prompt).toContain('-하고');
    expect(prompt).toContain('and / with');
    expect(prompt).toContain('Connect nouns with "and".');
  });

  it('falls back to placeholder text when hangul/grammar are empty', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, hangul: [], grammar: [] });
    expect(prompt).toContain('none retrieved');
  });

  it('requires the exact count for sentences and allows optional candidates', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'sentences', count: 7 });
    expect(prompt).toContain('Exactly 7 beginner sentence(s) in "sentences".');
    expect(prompt).toContain('"sentences":');
    expect(prompt).toContain('vocabulary_candidates" is optional');
  });

  it('requires the exact count for questions', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'questions', count: 3 });
    expect(prompt).toContain('Exactly 3 beginner question(s) in "questions".');
    expect(prompt).toContain('"questions":');
  });

  it('requires the exact count for fill_in_blank', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'fill_in_blank', count: 4 });
    expect(prompt).toContain('Exactly 4 fill-in-the-blank item(s) in "fill_in_blank".');
    expect(prompt).toContain('"fill_in_blank":');
  });

  it('caps the story sentence count instead of requiring an exact count', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'story', count: 6 });
    expect(prompt).toContain('at most 6 sentence(s)');
    expect(prompt).toContain('"story":');
  });

  it('emits only vocabulary_candidates as the primary payload for the candidates type, with no optional-candidates line', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'vocabulary_candidates', count: 8 });
    expect(prompt).toContain('Exactly 8 vocabulary candidate(s) in "vocabulary_candidates"');
    expect(prompt).not.toContain('is optional');
    expect(prompt).not.toContain('"sentences"');
    expect(prompt).not.toContain('"questions"');
    expect(prompt).not.toContain('"fill_in_blank"');
    expect(prompt).not.toContain('"story"');
  });

  it('clamps non-positive counts to at least 1', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, exerciseType: 'sentences', count: 0 });
    expect(prompt).toContain('Exactly 1 beginner sentence(s)');
  });

  it('omits the grammar summary line when the level has none', () => {
    const prompt = buildPracticeSystemPrompt({ ...baseOptions, level: { label: 'Korean 1A', guidance: 'Keep it simple.' } });
    expect(prompt).toContain('Keep it simple.');
    expect(prompt).toContain('valid JSON');
  });
});
