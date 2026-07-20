import type { PageServerLoad } from './$types';

import { aiEnabled } from '$lib/config';
import { educationCrumbs } from '$lib/education-nav';
import { loadLevelsConfig, loadPracticeThemes } from '$lib/data/loader';

export const prerender = true;

export const load: PageServerLoad = () => {
  const { default: defaultLevel, levels } = loadLevelsConfig();
  const themes = loadPracticeThemes();

  return {
    levels,
    themes,
    defaultLevel,
    aiEnabled,
    breadcrumbs: educationCrumbs({ label: 'Practice' }),
  };
};
