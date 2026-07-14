import { describe, expect, it } from 'vitest';

import { buildDeckKey, cardId, createProgress, filterDeck, filterStillLearning, shuffle } from './flashcards';

describe('flashcards helpers', () => {
  it('builds card ids and deck keys', () => {
    expect(cardId('학교', 'hak-gyo')).toBe('학교::hak-gyo');
    expect(buildDeckKey('registry', false)).toBe('registry:all');
    expect(buildDeckKey('family', true)).toBe('family:unknown');
  });

  it('creates empty progress', () => {
    expect(createProgress('registry:all')).toEqual({
      known: [],
      unknown: [],
      deckKey: 'registry:all',
      index: 0,
    });
  });

  it('filters unknown-only and still-learning decks', () => {
    const cards = [
      { id: 'a', hangul: '가', romanization: 'ga', english: 'a', source: 'registry' },
      { id: 'b', hangul: '나', romanization: 'na', english: 'b', source: 'registry' },
      { id: 'c', hangul: '다', romanization: 'da', english: 'c', source: 'registry' },
    ];
    const progress = {
      known: ['a'],
      unknown: ['b'],
      deckKey: 'registry:all',
      index: 0,
    };
    expect(filterDeck(cards, true, progress).map((c) => c.id)).toEqual(['b']);
    expect(filterStillLearning(cards, progress).map((c) => c.id)).toEqual(['b', 'c']);
    expect(filterDeck(cards, false, progress)).toEqual(cards);
  });

  it('shuffles without dropping items', () => {
    const items = [1, 2, 3, 4, 5];
    const shuffled = shuffle(items);
    expect(shuffled).toHaveLength(items.length);
    expect([...shuffled].sort()).toEqual(items);
    expect(items).toEqual([1, 2, 3, 4, 5]);
  });
});
