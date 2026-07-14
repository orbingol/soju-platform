import type { PageServerLoad } from './$types';

import { educationCrumbs } from '$lib/education-nav';
import { buildDeckKey } from '$lib/flashcards';
import { loadFlashcardDeck, loadTopics } from '$lib/data/loader';

export const prerender = true;

export function entries() {
  const topics = loadTopics();
  return [...topics.map((topic) => ({ source: topic.id })), { source: 'registry' }];
}

export const load: PageServerLoad = ({ params }) => {
  const topics = loadTopics();
  const source = params.source;
  const valid = source === 'registry' || topics.some((topic) => topic.id === source) ? source : 'registry';

  const cards = loadFlashcardDeck(valid);

  return {
    topics,
    source: valid,
    cards,
    deckKey: buildDeckKey(valid, false),
    breadcrumbs: educationCrumbs({ label: 'Flashcards' }),
  };
};
