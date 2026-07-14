import { describe, expect, it } from 'vitest';

import { buildEducationFallbackCrumbs, buildEducationNavItems, isVocabularyPath } from './education-nav';

describe('education-nav', () => {
  it('detects vocabulary paths', () => {
    expect(isVocabularyPath('/education/words/nouns')).toBe(true);
    expect(isVocabularyPath('/education/topics/family')).toBe(true);
    expect(isVocabularyPath('/education/flashcards/registry')).toBe(false);
  });

  it('includes practice only when AI is enabled', () => {
    const withAi = buildEducationNavItems('Soju', '/education/', true);
    const withoutAi = buildEducationNavItems('Soju', '/education/', false);
    expect(withAi.some((item) => item.label === 'Practice')).toBe(true);
    expect(withoutAi.some((item) => item.label === 'Practice')).toBe(false);
  });

  it('builds fallback crumbs for topics and grammar', () => {
    const topicCrumbs = buildEducationFallbackCrumbs('/education/topics/family', 'family', 'Family');
    expect(topicCrumbs.map((c) => c.label)).toEqual(expect.arrayContaining(['Education', 'Vocabulary', 'Topics', 'Family']));
    const grammarCrumbs = buildEducationFallbackCrumbs('/education/grammar/particles', 'particles');
    expect(grammarCrumbs.map((c) => c.label)).toEqual(expect.arrayContaining(['Education', 'Vocabulary', 'Grammar']));
  });
});
