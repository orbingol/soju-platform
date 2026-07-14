import type { PageServerLoad } from './$types';

import { vocabularyCrumbs, grammarHref } from '$lib/education-nav';
import { loadGrammarCategories } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  const categories = loadGrammarCategories();

  return {
    categories,
    breadcrumbs: vocabularyCrumbs({ label: 'Grammar', href: grammarHref }),
  };
};
