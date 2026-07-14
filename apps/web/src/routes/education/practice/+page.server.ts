import type { PageServerLoad } from './$types';

import { aiEnabled } from '$lib/config';
import { educationCrumbs } from '$lib/education-nav';
import { buildVocabularySummary } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  const vocabulary = buildVocabularySummary();

  return {
    vocabulary,
    aiEnabled,
    breadcrumbs: educationCrumbs({ label: 'Practice' }),
  };
};
