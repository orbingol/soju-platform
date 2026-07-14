import type { EntryGenerator, PageServerLoad } from './$types';
import { error } from '@sveltejs/kit';

import { vocabularyCrumbs, grammarHref } from '$lib/education-nav';
import { loadGrammarCategories, loadGrammarPatternPage, loadGrammarPatterns, loadGrammarPatternsByCategory, resolveGrammarCategory } from '$lib/data/loader';

export const prerender = true;

export const entries: EntryGenerator = () => {
  const categories = loadGrammarCategories().map((category) => ({ slug: category.slug }));
  const patterns = loadGrammarPatterns().map((pattern) => ({ slug: pattern.id }));
  return [...categories, ...patterns];
};

export const load: PageServerLoad = ({ params }) => {
  const category = resolveGrammarCategory(params.slug);
  if (category) {
    return {
      mode: 'category' as const,
      category,
      patterns: loadGrammarPatternsByCategory(category.id),
      breadcrumbs: vocabularyCrumbs({ label: 'Grammar', href: grammarHref }, { label: category.label }),
    };
  }

  const patternMeta = loadGrammarPatterns().find((p) => p.id === params.slug);
  if (!patternMeta) {
    error(404, `Unknown grammar page: ${params.slug}`);
  }

  const page = loadGrammarPatternPage(params.slug);
  const categoryInfo = resolveGrammarCategory(page.category);

  return {
    mode: 'pattern' as const,
    page,
    category: categoryInfo,
    breadcrumbs: vocabularyCrumbs(
      { label: 'Grammar', href: grammarHref },
      categoryInfo ? { label: categoryInfo.label, href: `${grammarHref}${categoryInfo.slug}/` } : { label: page.form },
      ...(categoryInfo ? [{ label: page.form }] : []),
    ),
  };
};
