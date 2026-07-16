import { base } from '$app/paths';

import type { Crumb } from '$lib/components/breadcrumb';
import type { NavItem } from '$lib/nav';

export const educationHref = `${base}/education/`;
export const vocabularyHref = `${base}/education/vocabulary/`;
export const wordTypesHref = `${base}/education/words/`;
export const verbsHref = `${base}/education/words/verbs/`;
export const topicsHref = `${base}/education/topics/`;
export const grammarHref = `${base}/education/grammar/`;
export const flashcardsHref = `${base}/education/flashcards/registry/`;
export const practiceHref = `${base}/education/practice/`;

export function isVocabularyPath(pathname: string): boolean {
  return pathname.includes('/education/vocabulary') || pathname.includes('/education/words') || pathname.includes('/education/topics') || pathname.includes('/education/grammar');
}

export function buildEducationNavItems(siteTitle: string, pathname: string, aiEnabled: boolean): NavItem[] {
  const vocabCurrent = isVocabularyPath(pathname);
  const wordTypesCurrent = pathname.includes('/education/words');
  const topicsCurrent = pathname.includes('/education/topics');
  const grammarCurrent = pathname.includes('/education/grammar');

  return [
    {
      label: `${siteTitle} Education`,
      href: educationHref,
      current: pathname === educationHref || pathname === `${base}/education`,
    },
    {
      label: 'Vocabulary',
      href: vocabularyHref,
      current: vocabCurrent,
      children: [
        { label: 'Word types', href: wordTypesHref, current: wordTypesCurrent },
        { label: 'Grammar', href: grammarHref, current: grammarCurrent },
        { label: 'Topics', href: topicsHref, current: topicsCurrent },
      ],
    },
    {
      label: 'Flashcards',
      href: flashcardsHref,
      current: pathname.includes('/education/flashcards'),
    },
    ...(aiEnabled
      ? [
          {
            label: 'Practice',
            href: practiceHref,
            current: pathname.includes('/education/practice'),
          },
        ]
      : []),
  ];
}

export function educationCrumbs(...segments: Crumb[]): Crumb[] {
  return [{ label: 'Home', href: `${base}/` }, { label: 'Education', href: educationHref }, ...segments];
}

export function vocabularyCrumbs(...segments: Crumb[]): Crumb[] {
  return educationCrumbs({ label: 'Vocabulary', href: vocabularyHref }, ...segments);
}

export function buildEducationFallbackCrumbs(pathname: string, section: string, topicLabel?: string): Crumb[] {
  if (pathname.includes('/education/vocabulary')) {
    return educationCrumbs({ label: 'Vocabulary' });
  }

  if (pathname.includes('/education/words/verbs')) {
    return vocabularyCrumbs({ label: 'Word types', href: wordTypesHref }, { label: 'Verbs' });
  }

  if (pathname.includes('/education/words/') && section && section !== 'words') {
    return vocabularyCrumbs({ label: 'Word types', href: wordTypesHref }, { label: topicLabel ?? section });
  }

  if (pathname.includes('/education/words')) {
    return vocabularyCrumbs({ label: 'Word types' });
  }

  if (pathname.includes('/education/topics/') && section && section !== 'topics') {
    return vocabularyCrumbs({ label: 'Topics', href: topicsHref }, { label: topicLabel ?? section });
  }

  if (pathname.includes('/education/topics')) {
    return vocabularyCrumbs({ label: 'Topics' });
  }

  if (pathname.includes('/education/grammar/') && section && section !== 'grammar') {
    const category = section;
    // Prefer showing Grammar > Category when possible; pattern labels come from loaders.
    return vocabularyCrumbs({ label: 'Grammar', href: grammarHref }, { label: topicLabel ?? category });
  }

  if (pathname.includes('/education/grammar')) {
    return vocabularyCrumbs({ label: 'Grammar' });
  }

  if (pathname.includes('/education/flashcards')) {
    return educationCrumbs({ label: 'Flashcards' });
  }

  if (pathname.includes('/education/practice')) {
    return educationCrumbs({ label: 'Practice' });
  }

  return educationCrumbs();
}
