import { error } from '@sveltejs/kit';
import type { EntryGenerator, PageServerLoad } from './$types';

import { vocabularyCrumbs, topicsHref } from '$lib/education-nav';
import { loadTopicPage, loadTopics } from '$lib/data/loader';

export const prerender = true;

export const entries: EntryGenerator = () => {
  return loadTopics().map((topic) => ({ topic: topic.id }));
};

export const load: PageServerLoad = ({ params }) => {
  try {
    const page = loadTopicPage(params.topic);
    return {
      ...page,
      breadcrumbs: vocabularyCrumbs({ label: 'Topics', href: topicsHref }, { label: page.meta.label }),
    };
  } catch (err) {
    error(404, err instanceof Error ? err.message : `Unknown topic: ${params.topic}`);
  }
};
