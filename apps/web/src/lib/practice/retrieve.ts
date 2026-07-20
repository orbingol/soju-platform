import fs from 'node:fs';
import path from 'node:path';

import { loadLevelsConfig } from '$lib/data/loader';
import { getDataDir } from '$lib/data/paths';
import type { LevelConfig } from '$lib/data/types';

import { cosineSimilarity } from './cosine';

/** Retrieval failure carrying the HTTP status the API route should return. */
export class PracticeRetrieveError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'PracticeRetrieveError';
    this.status = status;
  }
}

export interface RetrievedGrammar {
  id: string;
  form: string;
  english: string;
  summary?: string;
}

export interface PracticeRetrieveResult {
  hangul: string[];
  grammar: RetrievedGrammar[];
}

export interface PracticeRetrieveRequest {
  level?: string;
  queryVector: number[];
  vocabK?: number;
  grammarM?: number;
}

interface CachedVocabRecord {
  id: string;
  hangul: string;
  romanization: string;
  english: string;
  type: string;
  level: string | null;
  embedding: number[];
}

interface CachedGrammarRecord {
  id: string;
  form: string;
  english: string;
  category: string;
  summary: string;
  embedding: number[];
}

interface EmbeddingsMeta {
  embed_model: string;
  dimension: number | null;
  vocab_count: number;
  grammar_count: number;
}

interface EmbeddingsCache {
  meta: EmbeddingsMeta;
  vocab: CachedVocabRecord[];
  grammar: CachedGrammarRecord[];
}

const DEFAULT_VOCAB_K = 40;
const DEFAULT_GRAMMAR_M = 8;
const MAX_RESULT_COUNT = 200;

const EMBED_INDEX_HINT = 'Run `uv run poe embed-index` (requires Ollama) to build data/cache/embeddings/.';

function embeddingsCacheDir(dataDir: string): string {
  return path.join(dataDir, 'cache', 'embeddings');
}

function readJsonFile<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
}

function readJsonl<T>(filePath: string): T[] {
  return fs
    .readFileSync(filePath, 'utf8')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as T);
}

export function loadEmbeddingsCache(dataDir = getDataDir()): EmbeddingsCache {
  const cacheDir = embeddingsCacheDir(dataDir);
  const metaPath = path.join(cacheDir, 'meta.json');
  const vocabPath = path.join(cacheDir, 'vocab.jsonl');
  const grammarPath = path.join(cacheDir, 'grammar.jsonl');

  if (!fs.existsSync(metaPath) || !fs.existsSync(vocabPath) || !fs.existsSync(grammarPath)) {
    throw new PracticeRetrieveError(`Embedding cache not found. ${EMBED_INDEX_HINT}`, 503);
  }

  try {
    return {
      meta: readJsonFile<EmbeddingsMeta>(metaPath),
      vocab: readJsonl<CachedVocabRecord>(vocabPath),
      grammar: readJsonl<CachedGrammarRecord>(grammarPath)
    };
  } catch {
    throw new PracticeRetrieveError(`Embedding cache is corrupt. Rebuild it: ${EMBED_INDEX_HINT}`, 503);
  }
}

/** Mirror ``soju.levels._expand_level_ids``: level + ``include_levels`` parents, self included. */
function expandLevelIds(levelId: string, levels: LevelConfig[]): Set<string> {
  const byId = new Map(levels.map((level) => [level.id, level]));
  const seen = new Set<string>();

  function visit(id: string): void {
    if (seen.has(id)) return;
    seen.add(id);
    for (const parent of byId.get(id)?.includeLevels ?? []) {
      visit(parent);
    }
  }

  visit(levelId);
  return seen;
}

function clampCount(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return fallback;
  return Math.min(Math.floor(value), MAX_RESULT_COUNT);
}

/**
 * Rank cached vocabulary + grammar embeddings against a query vector for Practice generation.
 *
 * The query vector is embedded client-side (browser → Ollama `/api/embeddings`) so this
 * endpoint never needs its own Ollama base URL / Docker networking story — it only reads the
 * cache built by `soju embed-index` and computes cosine similarity.
 *
 * @throws {PracticeRetrieveError} 503 if the cache is missing/corrupt, 400 on a bad request or
 *   an embedding-dimension mismatch against the cached index.
 */
export function retrievePractice(request: PracticeRetrieveRequest, dataDir = getDataDir()): PracticeRetrieveResult {
  const { queryVector } = request;
  if (!Array.isArray(queryVector) || queryVector.length === 0 || !queryVector.every((value) => typeof value === 'number' && Number.isFinite(value))) {
    throw new PracticeRetrieveError('queryVector must be a non-empty array of numbers.', 400);
  }

  const cache = loadEmbeddingsCache(dataDir);
  if (cache.meta.dimension != null && queryVector.length !== cache.meta.dimension) {
    throw new PracticeRetrieveError(
      `Query embedding has dimension ${queryVector.length}, but the cached index has dimension ${cache.meta.dimension} ` +
        `(embed model ${cache.meta.embed_model}). Re-embed the theme with that model, or rebuild the index: ${EMBED_INDEX_HINT}`,
      400
    );
  }

  const levelsConfig = loadLevelsConfig(dataDir);
  const levelId = request.level ?? levelsConfig.default;
  if (!levelsConfig.levels.some((level) => level.id === levelId)) {
    const known = levelsConfig.levels.map((level) => level.id).join(', ');
    throw new PracticeRetrieveError(`Unknown level ${JSON.stringify(levelId)}. Known levels: ${known}`, 400);
  }
  const includedLevels = expandLevelIds(levelId, levelsConfig.levels);

  const vocabK = clampCount(request.vocabK, DEFAULT_VOCAB_K);
  const grammarM = clampCount(request.grammarM, DEFAULT_GRAMMAR_M);

  const rankedVocab = cache.vocab
    .filter((entry) => includedLevels.has(entry.level ?? levelsConfig.default))
    .map((entry) => ({ entry, score: cosineSimilarity(queryVector, entry.embedding) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, vocabK);

  const rankedGrammar = cache.grammar
    .map((entry) => ({ entry, score: cosineSimilarity(queryVector, entry.embedding) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, grammarM);

  return {
    hangul: rankedVocab.map(({ entry }) => entry.hangul),
    grammar: rankedGrammar.map(({ entry }) => ({
      id: entry.id,
      form: entry.form,
      english: entry.english,
      ...(entry.summary ? { summary: entry.summary } : {})
    }))
  };
}
