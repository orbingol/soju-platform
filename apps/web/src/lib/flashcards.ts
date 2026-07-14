import { getItem, removeItem, setItem } from '$lib/storage';

export interface Flashcard {
  id: string;
  hangul: string;
  romanization: string;
  english: string;
  source: string;
}

export interface FlashcardProgress {
  known: string[];
  unknown: string[];
  deckKey: string;
  index: number;
}

const PROGRESS_KEY = 'flashcards-progress';

export const FLASHCARDS_PROGRESS_CLEARED = 'soju:flashcards-progress-cleared';

export function cardId(hangul: string, romanization: string): string {
  return `${hangul}::${romanization}`;
}

export function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function buildDeckKey(source: string, unknownOnly: boolean): string {
  return `${source}:${unknownOnly ? 'unknown' : 'all'}`;
}

export function filterDeck(cards: Flashcard[], unknownOnly: boolean, progress: FlashcardProgress | null): Flashcard[] {
  if (!unknownOnly || !progress) return cards;
  const unknown = new Set(progress.unknown);
  return cards.filter((card) => unknown.has(card.id));
}

/** Cards not marked known — includes "still learning" and not-yet-reviewed. */
export function filterStillLearning(cards: Flashcard[], progress: FlashcardProgress | null): Flashcard[] {
  if (!progress) return cards;
  const known = new Set(progress.known);
  return cards.filter((card) => !known.has(card.id));
}

export async function loadProgress(): Promise<FlashcardProgress | null> {
  return getItem<FlashcardProgress>(PROGRESS_KEY);
}

export async function saveProgress(progress: FlashcardProgress): Promise<void> {
  await setItem(PROGRESS_KEY, progress);
}

export async function markCard(progress: FlashcardProgress, cardIdValue: string, known: boolean): Promise<FlashcardProgress> {
  const knownSet = new Set(progress.known);
  const unknownSet = new Set(progress.unknown);

  if (known) {
    knownSet.add(cardIdValue);
    unknownSet.delete(cardIdValue);
  } else {
    unknownSet.add(cardIdValue);
    knownSet.delete(cardIdValue);
  }

  const next: FlashcardProgress = {
    ...progress,
    known: [...knownSet],
    unknown: [...unknownSet],
  };

  await saveProgress(next);
  return next;
}

export function createProgress(deckKey: string): FlashcardProgress {
  return {
    known: [],
    unknown: [],
    deckKey,
    index: 0,
  };
}

export async function clearProgress(): Promise<void> {
  await removeItem(PROGRESS_KEY);
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(FLASHCARDS_PROGRESS_CLEARED));
  }
}
