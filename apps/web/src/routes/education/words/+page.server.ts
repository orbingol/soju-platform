import type { PageServerLoad } from './$types';

import { vocabularyCrumbs, wordTypesHref } from '$lib/education-nav';
import { loadTypes } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  const types = loadTypes().filter((type) => type.id !== 'phrase');

  return {
    types,
    breadcrumbs: vocabularyCrumbs({ label: 'Word types', href: wordTypesHref }),
  };
};
