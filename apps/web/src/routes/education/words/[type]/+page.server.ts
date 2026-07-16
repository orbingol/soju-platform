import { error, redirect } from '@sveltejs/kit';
import type { EntryGenerator, PageServerLoad } from './$types';
import { base } from '$app/paths';

import { vocabularyCrumbs, wordTypesHref } from '$lib/education-nav';
import { loadTopics, loadTypePage, typeSlugsForPrerender } from '$lib/data/loader';

export const prerender = true;

export const entries: EntryGenerator = () => {
  const types = typeSlugsForPrerender().map((type) => ({ type }));
  const topics = loadTopics().map((topic) => ({ type: topic.id }));
  const seen = new Set<string>();
  return [...types, ...topics].filter(({ type }) => {
    if (seen.has(type)) return false;
    seen.add(type);
    return true;
  });
};

export const load: PageServerLoad = ({ params }) => {
  const topicIds = new Set(loadTopics().map((t) => t.id));
  if (topicIds.has(params.type)) {
    redirect(301, `${base}/education/topics/${params.type}/`);
  }

  try {
    const page = loadTypePage(params.type);
    return {
      ...page,
      breadcrumbs: vocabularyCrumbs({ label: 'Word types', href: wordTypesHref }, { label: page.type.label }),
    };
  } catch (err) {
    error(404, err instanceof Error ? err.message : `Unknown type: ${params.type}`);
  }
};
