import type { PageServerLoad } from './$types';

import { educationCrumbs } from '$lib/education-nav';

export const prerender = true;

export const load: PageServerLoad = () => ({
  breadcrumbs: educationCrumbs({ label: 'Vocabulary' }),
});
