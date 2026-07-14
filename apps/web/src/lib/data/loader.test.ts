import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

import {
  buildVocabularySummary,
  grammarCategoryHref,
  loadFlashcardDeck,
  loadGrammarCategories,
  loadGrammarPatternPage,
  loadGrammarPatterns,
  loadTopicPage,
  loadTopics,
  loadTopicTable,
  loadTypePage,
  loadTypes,
  loadVocabulary,
  matchesVocabularySearch,
  resolveGrammarCategory,
  resolveTypeBySlug,
  resolveVerbCell,
  typeSlugsForPrerender
} from './loader';
import type { VerbEntry } from './types';

const DATA_DIR = path.resolve(import.meta.dirname, '../../../../../data');

describe('loader', () => {
  it('resolves content layout paths under data/content', () => {
    expect(fs.existsSync(path.join(DATA_DIR, 'content', 'registry', 'vocabulary.yaml'))).toBe(true);
    expect(fs.existsSync(path.join(DATA_DIR, 'content', 'verbs', 'manifest.yaml'))).toBe(true);
    expect(fs.existsSync(path.join(DATA_DIR, 'content', 'topics', 'family', 'topic.yaml'))).toBe(true);
  });

  it('loads verbs with forms and examples', () => {
    const { entries, table } = loadTypePage('verbs', DATA_DIR);
    expect(entries.length).toBeGreaterThan(0);
    expect('sections' in table && table.sections.length).toBeGreaterThan(0);

    const meokda = entries.find((v) => v.hangul === '먹다');
    expect(meokda).toBeDefined();
    if (meokda && 'forms' in meokda) {
      expect(meokda.forms.present?.casual_polite).toBe('먹어요');
      expect(meokda.examples?.present?.casual_polite?.length).toBeGreaterThan(0);
    }
  });

  it('loads family topic with sections', () => {
    const { sections, meta } = loadTopicPage('family', DATA_DIR);
    expect(meta.id).toBe('family');
    expect(meta.label.length).toBeGreaterThan(0);
    expect(sections.length).toBeGreaterThanOrEqual(1);
    const entries = sections.flatMap((s) => s.entries);
    expect(entries.length).toBeGreaterThan(0);
    expect(sections.map((s) => s.id)).toEqual(
      expect.arrayContaining(['parents', 'siblings', 'children'])
    );
  });

  it('shows verb tense examples on topic pages', () => {
    const { sections } = loadTopicPage('common', DATA_DIR);
    const everyday = sections.find((s) => s.id === 'everyday');
    expect(everyday).toBeDefined();
    const verb = everyday?.entries.find((e) => e.hangul === '먹다');
    expect(verb).toBeDefined();
    expect(verb?.examples?.length).toBeGreaterThan(0);
  });

  it('loads grammar patterns with sections', () => {
    const patterns = loadGrammarPatterns(DATA_DIR);
    expect(patterns.length).toBeGreaterThan(0);
    const hago = loadGrammarPatternPage('hago', DATA_DIR);
    expect(hago.form).toContain('하고');
    expect(hago.sections.length).toBeGreaterThan(0);
    expect(hago.conversations?.length).toBeGreaterThan(0);
    expect(hago.conversations?.[0].turns.length).toBeGreaterThanOrEqual(4);
  });

  it('includes question words category', () => {
    const questions = loadGrammarPatterns(DATA_DIR).filter((p) => p.category === 'question_words');
    expect(questions.map((p) => p.id)).toEqual(
      expect.arrayContaining(['museun', 'eonje', 'wae', 'eolmana'])
    );
  });

  it('loads types and hides phrases/verbs from type prerender slugs', () => {
    const types = loadTypes(DATA_DIR);
    expect(types.map((t) => t.slug)).toEqual(expect.arrayContaining(['nouns', 'verbs', 'phrases']));
    expect(resolveTypeBySlug('nouns', DATA_DIR)?.id).toBe('noun');
    const slugs = typeSlugsForPrerender(DATA_DIR);
    expect(slugs).not.toContain('verbs');
    expect(slugs).not.toContain('phrases');
    expect(slugs).toContain('nouns');
  });

  it('excludes hidden and phrase entries from browsable type pages', () => {
    const { entries } = loadTypePage('phrases', DATA_DIR);
    expect(entries.length).toBe(0);

    const nouns = loadTypePage('nouns', DATA_DIR).entries;
    expect(nouns.every((e) => e.visibility !== 'hidden' && e.type !== 'phrase')).toBe(true);
  });

  it('loads topics without requiring manifest path', () => {
    const topics = loadTopics(DATA_DIR);
    expect(topics.length).toBeGreaterThan(0);
    expect(topics.every((t) => t.id && t.label && !('path' in t))).toBe(true);
  });

  it('uses numbers topic table override when present', () => {
    const overridePath = path.join(DATA_DIR, 'content', 'topics', 'numbers', 'table.yaml');
    if (!fs.existsSync(overridePath)) return;
    const table = loadTopicTable('numbers', DATA_DIR);
    const defaultTable = loadTopicTable('family', DATA_DIR);
    expect(table).toBeDefined();
    expect(defaultTable).toBeDefined();
  });

  it('builds flashcard decks for registry and topics', () => {
    const registry = loadFlashcardDeck('registry', DATA_DIR);
    expect(registry.length).toBeGreaterThan(0);
    expect(registry.every((c) => c.source === 'registry')).toBe(true);

    const family = loadFlashcardDeck('family', DATA_DIR);
    expect(family.length).toBeGreaterThan(0);
    expect(family.every((c) => c.source === 'family')).toBe(true);
  });

  it('resolves verb cells for normal and combined columns', () => {
    const verb = loadTypePage('verbs', DATA_DIR).entries.find((v) => v.hangul === '먹다') as VerbEntry;
    expect(verb).toBeDefined();
    const cell = resolveVerbCell(verb, 'present', {
      variant: 'casual_polite',
      label: 'Casual',
      subtitle: '해요'
    });
    expect(cell.form).toBe('먹어요');

    const combined = resolveVerbCell(verb, 'present', {
      variant: 'combined',
      label: 'Both',
      subtitle: '',
      join: ['casual_polite', 'formal_polite'],
      separator: ' / '
    });
    expect(combined.form).toContain('먹어요');
    expect(combined.form).toContain('먹습니다');
  });

  it('matches vocabulary search across hangul, english, romanization, and forms', () => {
    const entry = {
      hangul: '먹다',
      romanization: 'meok-da',
      english: 'to eat',
      forms: { present: { casual_polite: '먹어요' } }
    };
    expect(matchesVocabularySearch(entry, '')).toBe(true);
    expect(matchesVocabularySearch(entry, '먹')).toBe(true);
    expect(matchesVocabularySearch(entry, 'eat')).toBe(true);
    expect(matchesVocabularySearch(entry, 'meokda')).toBe(true);
    expect(matchesVocabularySearch(entry, '먹어요')).toBe(true);
    expect(matchesVocabularySearch(entry, 'zzzz')).toBe(false);
  });

  it('loads grammar categories and hrefs', () => {
    const categories = loadGrammarCategories();
    expect(categories.length).toBeGreaterThan(0);
    expect(resolveGrammarCategory('question_words')?.slug).toBe('question-words');
    expect(grammarCategoryHref('question_words')).toBe('/education/grammar/question-words/');
  });

  it('builds vocabulary summary including phrases for practice', () => {
    const summary = buildVocabularySummary(DATA_DIR);
    expect(summary.verbs.length).toBeGreaterThan(0);
    expect(summary.words.length).toBeGreaterThan(0);
    // Practice/chat summary includes every non-verb type (phrases stay available).
    expect(loadTypes(DATA_DIR).some((t) => t.id === 'phrase')).toBe(true);
    const phrases = loadVocabulary(DATA_DIR).filter((e) => e.type === 'phrase');
    expect(phrases.length).toBeGreaterThan(0);
    const summaryHangul = new Set(summary.words.map((w) => w.hangul));
    expect(phrases.every((p) => summaryHangul.has(p.hangul))).toBe(true);
  });

  it('throws on unknown topic and type', () => {
    expect(() => loadTopicPage('does-not-exist', DATA_DIR)).toThrow(/Unknown topic/);
    expect(() => loadTypePage('does-not-exist', DATA_DIR)).toThrow(/Unknown type/);
  });
});
