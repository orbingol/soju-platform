import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

import { vocabularyCrumbs, wordTypesHref } from '$lib/education-nav';
import { loadTypePage } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  try {
    const page = loadTypePage('verbs');
    return {
      ...page,
      breadcrumbs: vocabularyCrumbs({ label: 'Word types', href: wordTypesHref }, { label: page.type.label }),
    };
  } catch (err) {
    error(404, err instanceof Error ? err.message : 'Verb type not found');
  }
};
