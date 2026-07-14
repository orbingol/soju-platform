import type { PageServerLoad } from './$types';

import { vocabularyCrumbs, topicsHref } from '$lib/education-nav';
import { loadTopics } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  const topics = loadTopics();

  return {
    topics,
    breadcrumbs: vocabularyCrumbs({ label: 'Topics', href: topicsHref }),
  };
};
