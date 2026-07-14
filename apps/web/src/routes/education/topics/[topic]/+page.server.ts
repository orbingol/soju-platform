import { vocabularyCrumbs, topicsHref } from '$lib/education-nav';
import { loadTopicPage, loadTopics } from '$lib/data/loader';

export const prerender = true;

export function entries() {
  return loadTopics().map((topic) => ({ topic: topic.id }));
}

export const load = ({ params }) => {
  const page = loadTopicPage(params.topic);

  return {
    ...page,
    breadcrumbs: vocabularyCrumbs({ label: 'Topics', href: topicsHref }, { label: page.meta.label }),
  };
};
