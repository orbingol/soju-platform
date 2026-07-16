import fs from 'node:fs';
import path from 'node:path';
import yaml from 'yaml';

import {
  assertSafeSlug,
  contentDir,
  displayDataPath,
  getDataDir,
  grammarDir,
  registryDir,
  resolveUnder,
  topicsDir,
  verbsDir
} from './paths';
import type {
  ConjugationColumn,
  DefaultTableLayout,
  Example,
  GrammarCategory,
  GrammarCategoryInfo,
  GrammarPatternMeta,
  GrammarPatternPage,
  ResolvedEntry,
  TopicEntry,
  TopicEntryLocal,
  TopicMeta,
  TopicSection,
  VerbEntry,
  VerbTableLayout,
  VocabularyEntry,
  VocabularyType
} from './types';

const HIDDEN_TYPE_SLUGS = new Set(['phrases']);

function isBrowsableVocabulary(entry: VocabularyEntry): boolean {
  if (entry.visibility === 'hidden') return false;
  if (entry.type === 'phrase') return false;
  return true;
}

function readYaml<T>(filePath: string, dataDir: string): T {
  const label = displayDataPath(filePath, dataDir);
  let raw: string;
  try {
    raw = fs.readFileSync(filePath, 'utf8');
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code === 'ENOENT') {
      throw new Error(`Missing data file: ${label}`);
    }
    throw new Error(`Failed to read data file: ${label}`);
  }

  try {
    return yaml.parse(raw) as T;
  } catch {
    throw new Error(`Malformed YAML: ${label}`);
  }
}

export function loadTypes(dataDir = getDataDir()): VocabularyType[] {
  const data = readYaml<{ types: VocabularyType[] }>(
    path.join(registryDir(dataDir), 'types.yaml'),
    dataDir,
  );
  return data.types;
}

export function resolveTypeBySlug(slug: string, dataDir = getDataDir()): VocabularyType | undefined {
  return loadTypes(dataDir).find((t) => t.slug === slug);
}

export function loadVocabulary(dataDir = getDataDir()): VocabularyEntry[] {
  return readYaml<VocabularyEntry[]>(path.join(registryDir(dataDir), 'vocabulary.yaml'), dataDir);
}

export function loadExamplesStore(dataDir = getDataDir()): Record<string, unknown> {
  return readYaml<Record<string, unknown>>(path.join(registryDir(dataDir), 'examples.yaml'), dataDir);
}

function defaultExamplesFor(vocabId: string, store: Record<string, unknown>): Example[] {
  const entry = store[vocabId];
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return [];
  const obj = entry as Record<string, unknown>;
  const defaults = obj.default;
  if (!Array.isArray(defaults)) return [];
  return defaults as Example[];
}

function topicExamplesFor(
  vocab: VocabularyEntry,
  store: Record<string, unknown>
): Example[] {
  const defaults = defaultExamplesFor(vocab.id, store);
  if (defaults.length > 0) return defaults;
  if (vocab.type !== 'verb') return [];

  const verbExamples = verbExamplesFor(vocab.id, store);
  if (!verbExamples) return [];

  for (const tense of ['present', 'past', 'future']) {
    const variants = verbExamples[tense];
    if (!variants) continue;
    for (const variant of ['casual_polite', 'formal_polite']) {
      const examples = variants[variant];
      if (examples?.length) return examples;
    }
  }
  return [];
}

function verbExamplesFor(
  vocabId: string,
  store: Record<string, unknown>
): Record<string, Record<string, Example[]>> | undefined {
  const entry = store[vocabId];
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return undefined;
  const obj = entry as Record<string, unknown>;
  if ('default' in obj) return undefined;
  const result: Record<string, Record<string, Example[]>> = {};
  for (const [tense, variants] of Object.entries(obj)) {
    if (variants && typeof variants === 'object' && !Array.isArray(variants)) {
      result[tense] = variants as Record<string, Example[]>;
    }
  }
  return Object.keys(result).length > 0 ? result : undefined;
}

export function loadTypeTable(typeId: string, dataDir = getDataDir()): VerbTableLayout | DefaultTableLayout {
  assertSafeSlug(typeId, 'type id');
  const content = contentDir(dataDir);
  const specialized =
    typeId === 'verb'
      ? resolveUnder(content, 'verbs', 'table.yaml')
      : resolveUnder(content, typeId, 'table.yaml');
  if (fs.existsSync(specialized)) {
    return readYaml<VerbTableLayout>(specialized, dataDir);
  }
  return readYaml<DefaultTableLayout>(resolveUnder(content, 'words', 'table.yaml'), dataDir);
}

export function loadTopicTable(topicId: string, dataDir = getDataDir()): DefaultTableLayout {
  assertSafeSlug(topicId, 'topic id');
  const topics = topicsDir(dataDir);
  const override = resolveUnder(topics, topicId, 'table.yaml');
  if (fs.existsSync(override)) {
    return readYaml<DefaultTableLayout>(override, dataDir);
  }
  return readYaml<DefaultTableLayout>(resolveUnder(topics, 'table.yaml'), dataDir);
}

function loadAllVerbForms(
  dataDir: string
): Record<string, Record<string, Record<string, string>>> {
  const verbs = verbsDir(dataDir);
  const manifest = readYaml<{ forms: Record<string, string> }>(
    path.join(verbs, 'manifest.yaml'),
    dataDir,
  );
  const byTense: Record<string, Record<string, Record<string, string>>> = {};
  for (const [tense, rel] of Object.entries(manifest.forms)) {
    byTense[tense] = readYaml<Record<string, Record<string, string>>>(
      resolveUnder(verbs, rel),
      dataDir,
    );
  }
  return byTense;
}

function resolveVerbForms(
  vocabId: string,
  formsByTense: Record<string, Record<string, Record<string, string>>>
): Record<string, Record<string, string>> {
  const forms: Record<string, Record<string, string>> = {};
  for (const [tense, file] of Object.entries(formsByTense)) {
    if (file[vocabId]) {
      forms[tense] = file[vocabId];
    }
  }
  return forms;
}

function resolveEntry(
  entry: TopicEntry,
  vocabularyById: Map<string, VocabularyEntry>,
  examplesStore: Record<string, unknown>
): ResolvedEntry {
  if ('ref' in entry) {
    const vocab = vocabularyById.get(entry.ref);
    if (!vocab) {
      throw new Error(`Dangling vocabulary ref: ${entry.ref}`);
    }
    return {
      id: vocab.id,
      hangul: vocab.hangul,
      romanization: vocab.romanization,
      english: vocab.english,
      type: vocab.type,
      examples: topicExamplesFor(vocab, examplesStore)
    };
  }
  const local = entry as TopicEntryLocal;
  return {
    id: local.id,
    hangul: local.hangul,
    romanization: local.romanization,
    english: local.english,
    type: local.type ?? 'noun',
    examples: local.examples
  };
}

export function loadTypePage(typeSlug: string, dataDir = getDataDir()) {
  assertSafeSlug(typeSlug, 'type slug');
  const type = resolveTypeBySlug(typeSlug, dataDir);
  if (!type) {
    throw new Error(`Unknown type slug: ${typeSlug}`);
  }

  const vocabulary = loadVocabulary(dataDir);
  const examplesStore = loadExamplesStore(dataDir);
  const table = loadTypeTable(type.id, dataDir);
  const entries = vocabulary.filter((v) => v.type === type.id && isBrowsableVocabulary(v));

  if (type.id === 'verb') {
    const formsByTense = loadAllVerbForms(dataDir);
    const verbs: VerbEntry[] = entries.map((entry) => ({
      ...entry,
      type: 'verb',
      forms: resolveVerbForms(entry.id, formsByTense),
      examples: verbExamplesFor(entry.id, examplesStore)
    }));
    return { type, entries: verbs, table: table as VerbTableLayout };
  }

  const resolved: ResolvedEntry[] = entries.map((entry) => ({
    ...entry,
    examples: defaultExamplesFor(entry.id, examplesStore)
  }));

  return { type, entries: resolved, table: table as DefaultTableLayout };
}

export function loadTopics(dataDir = getDataDir()): TopicMeta[] {
  const manifest = readYaml<{
    topics: Record<string, { label: string; description?: string }>;
  }>(path.join(topicsDir(dataDir), 'manifest.yaml'), dataDir);

  return Object.entries(manifest.topics).map(([id, topic]) => ({
    id,
    label: topic.label,
    description: topic.description
  }));
}

export function loadTopicPage(topicId: string, dataDir = getDataDir()) {
  assertSafeSlug(topicId, 'topic id');
  const manifest = readYaml<{
    topics: Record<string, { label: string; description?: string }>;
  }>(path.join(topicsDir(dataDir), 'manifest.yaml'), dataDir);
  const meta = manifest.topics[topicId];
  if (!meta) {
    throw new Error(`Unknown topic: ${topicId}`);
  }

  const topicData = readYaml<{ sections: Array<{ id: string; label: string; description?: string; entries: TopicEntry[] }> }>(
    resolveUnder(topicsDir(dataDir), topicId, 'topic.yaml'),
    dataDir,
  );
  const vocabularyById = new Map(loadVocabulary(dataDir).map((v) => [v.id, v]));
  const examplesStore = loadExamplesStore(dataDir);
  const table = loadTopicTable(topicId, dataDir);

  const sections: TopicSection[] = topicData.sections.map((section) => ({
    id: section.id,
    label: section.label,
    description: section.description,
    entries: section.entries.map((entry) => resolveEntry(entry, vocabularyById, examplesStore))
  }));

  return {
    meta: {
      id: topicId,
      label: meta.label,
      description: meta.description
    },
    sections,
    table
  };
}

export function loadFlashcardDeck(
  source: string,
  dataDir = getDataDir()
): Array<{ id: string; hangul: string; romanization: string; english: string; source: string }> {
  if (source === 'registry') {
    return loadVocabulary(dataDir)
      .filter((entry) => entry.type !== 'verb' && isBrowsableVocabulary(entry))
      .map((entry) => ({
        id: entry.id,
        hangul: entry.hangul,
        romanization: entry.romanization,
        english: entry.english,
        source: 'registry'
      }));
  }

  assertSafeSlug(source, 'flashcard source');
  const { sections } = loadTopicPage(source, dataDir);
  const entries = sections.flatMap((s) => s.entries);
  return entries.map((entry) => ({
    id: entry.id,
    hangul: entry.hangul,
    romanization: entry.romanization,
    english: entry.english,
    source
  }));
}

export function resolveVerbCell(
  verb: VerbEntry,
  sectionId: string,
  column: ConjugationColumn
): { form: string; examples: Example[] } {
  const tenseForms = verb.forms[sectionId] ?? {};
  const tenseExamples = verb.examples?.[sectionId] ?? {};

  if (column.variant === 'combined') {
    const join = column.join ?? [];
    let form = tenseForms.combined ?? '';
    if (!form && join.length > 0) {
      form = join
        .map((variant) => tenseForms[variant])
        .filter(Boolean)
        .join(column.separator ?? ' · ');
    }
    let examples = tenseExamples.combined ?? [];
    if (examples.length === 0 && join.length > 0) {
      examples = tenseExamples[join[0]] ?? [];
    }
    return { form, examples };
  }

  return {
    form: tenseForms[column.variant] ?? '',
    examples: tenseExamples[column.variant] ?? []
  };
}

function normalizeSearch(text: string): string {
  return text.toLowerCase().replace(/-/g, '');
}

export function matchesVocabularySearch(
  entry: { hangul: string; romanization: string; english: string; forms?: Record<string, Record<string, string>> },
  query: string
): boolean {
  const q = query.trim();
  if (!q) return true;
  const qLower = q.toLowerCase();
  const qNorm = normalizeSearch(qLower);
  if (entry.hangul.includes(q)) return true;
  if (entry.english.toLowerCase().includes(qLower)) return true;
  if (normalizeSearch(entry.romanization).includes(qNorm)) return true;
  if (entry.forms) {
    for (const tense of Object.values(entry.forms)) {
      for (const form of Object.values(tense)) {
        if (form.includes(q)) return true;
      }
    }
  }
  return false;
}

export function typeSlugsForPrerender(dataDir = getDataDir()): string[] {
  return loadTypes(dataDir)
    .map((t) => t.slug)
    .filter((slug) => slug !== 'verbs' && !HIDDEN_TYPE_SLUGS.has(slug));
}

const GRAMMAR_CATEGORIES: GrammarCategoryInfo[] = [
  {
    id: 'particles',
    slug: 'particles',
    label: 'Particles',
    description:
      'Little words that stick to nouns to show their job in the sentence — like “and/with”, “also”, “to someone”, or “by bus”. Korean uses particles instead of changing word order as much as English does.'
  },
  {
    id: 'time_place',
    slug: 'time-place',
    label: 'Time & place',
    description:
      'Patterns for when and where: “from … to …”, “for/during/while”, “after”, and floor numbers. They help you talk about schedules, duration, and locations.'
  },
  {
    id: 'verb_patterns',
    slug: 'verb-patterns',
    label: 'Verb patterns',
    description:
      'Endings and helpers that attach to verbs: making activity verbs with 하다, saying what you want (-고 싶어요), asking politely (-세요), or telling someone not to (-지 마세요).'
  },
  {
    id: 'question_words',
    slug: 'question-words',
    label: 'Question words',
    description:
      'Words that ask for information: what, when, why, how, and how long. Combine them with the patterns above to ask real questions in conversation.'
  },
  {
    id: 'connectors',
    slug: 'connectors',
    label: 'Connectors',
    description:
      'Words that link ideas between sentences — “and then”, “but”, “in that case”. They make conversation flow instead of sounding like a list of separate lines.'
  }
];

export function loadGrammarCategories(): GrammarCategoryInfo[] {
  return GRAMMAR_CATEGORIES;
}

export function resolveGrammarCategory(
  idOrSlug: string
): GrammarCategoryInfo | undefined {
  return GRAMMAR_CATEGORIES.find((c) => c.id === idOrSlug || c.slug === idOrSlug);
}

export function grammarCategoryLabel(category: GrammarCategory): string {
  return resolveGrammarCategory(category)?.label ?? category;
}

export function grammarCategoryHref(category: GrammarCategory, base = ''): string {
  const info = resolveGrammarCategory(category);
  const slug = info?.slug ?? category;
  return `${base}/education/grammar/${slug}/`;
}

export function loadGrammarPatterns(dataDir = getDataDir()): GrammarPatternMeta[] {
  const manifest = readYaml<{
    patterns: Record<
      string,
      {
        path: string;
        label: string;
        form: string;
        english: string;
        category: GrammarCategory;
        description?: string;
      }
    >;
  }>(path.join(grammarDir(dataDir), 'manifest.yaml'), dataDir);

  return Object.entries(manifest.patterns).map(([id, pattern]) => ({
    id,
    label: pattern.label,
    form: pattern.form,
    english: pattern.english,
    category: pattern.category,
    description: pattern.description,
    path: pattern.path
  }));
}

export function loadGrammarPatternsByCategory(
  category: GrammarCategory,
  dataDir = getDataDir()
): GrammarPatternMeta[] {
  return loadGrammarPatterns(dataDir).filter((p) => p.category === category);
}

export function loadGrammarPatternPage(patternId: string, dataDir = getDataDir()): GrammarPatternPage {
  assertSafeSlug(patternId, 'grammar pattern id');
  const patterns = loadGrammarPatterns(dataDir);
  const meta = patterns.find((p) => p.id === patternId);
  if (!meta) {
    throw new Error(`Unknown grammar pattern: ${patternId}`);
  }
  return readYaml<GrammarPatternPage>(resolveUnder(grammarDir(dataDir), meta.path), dataDir);
}

export function buildVocabularySummary(dataDir = getDataDir()): {
  words: Array<{ hangul: string; romanization: string; english: string }>;
  verbs: Array<{ hangul: string; romanization: string; english: string }>;
} {
  const vocabulary = loadVocabulary(dataDir);
  // Practice/chat use the full registry, including hidden grammar phrases.
  const words = vocabulary
    .filter((e) => e.type !== 'verb')
    .map((e) => ({ hangul: e.hangul, romanization: e.romanization, english: e.english }));
  const verbs = vocabulary
    .filter((e) => e.type === 'verb')
    .map((e) => ({ hangul: e.hangul, romanization: e.romanization, english: e.english }));
  return { words, verbs };
}
