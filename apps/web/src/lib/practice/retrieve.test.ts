import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import yaml from 'yaml';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { PracticeRetrieveError, loadEmbeddingsCache, retrievePractice } from './retrieve';

let dataDir: string;

function writeJsonl(filePath: string, records: unknown[]): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, records.map((r) => JSON.stringify(r)).join('\n') + '\n', 'utf8');
}

function setUpFixture(): void {
  const contentDir = path.join(dataDir, 'content');
  fs.mkdirSync(contentDir, { recursive: true });
  fs.writeFileSync(
    path.join(contentDir, 'levels.yaml'),
    yaml.stringify({
      default: '1A',
      levels: {
        '1A': { label: 'Korean 1A', description: 'Beginner', guidance: 'Keep it simple.' },
        '1B': {
          label: 'Korean 1B',
          description: 'High beginner',
          guidance: 'Slightly richer.',
          include_levels: ['1A']
        }
      }
    }),
    'utf8'
  );

  const cacheDir = path.join(dataDir, 'cache', 'embeddings');
  fs.mkdirSync(cacheDir, { recursive: true });
  fs.writeFileSync(
    path.join(cacheDir, 'meta.json'),
    JSON.stringify({ embed_model: 'mock-model', dimension: 2, vocab_count: 3, grammar_count: 1 }),
    'utf8'
  );
  writeJsonl(path.join(cacheDir, 'vocab.jsonl'), [
    { id: 'v1', hangul: '학교', romanization: 'hak-gyo', english: 'school', type: 'noun', level: null, embedding: [1, 0] },
    { id: 'v2', hangul: '사과', romanization: 'sa-gwa', english: 'apple', type: 'noun', level: '1B', embedding: [0, 1] },
    { id: 'v3', hangul: '물', romanization: 'mul', english: 'water', type: 'noun', level: '1A', embedding: [0.6, 0.8] }
  ]);
  writeJsonl(path.join(cacheDir, 'grammar.jsonl'), [
    { id: 'do', form: '-도', english: 'also / even', category: 'particles', summary: 'Additive particle.', embedding: [1, 0] }
  ]);
}

beforeEach(() => {
  dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'soju-retrieve-'));
  setUpFixture();
});

afterEach(() => {
  fs.rmSync(dataDir, { recursive: true, force: true });
});

describe('loadEmbeddingsCache', () => {
  it('throws a 503 PracticeRetrieveError when the cache is missing', () => {
    const emptyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'soju-retrieve-empty-'));
    try {
      expect(() => loadEmbeddingsCache(emptyDir)).toThrow(PracticeRetrieveError);
      try {
        loadEmbeddingsCache(emptyDir);
        expect.unreachable();
      } catch (err) {
        expect(err).toBeInstanceOf(PracticeRetrieveError);
        expect((err as PracticeRetrieveError).status).toBe(503);
        expect((err as PracticeRetrieveError).message).toMatch(/embed-index/);
      }
    } finally {
      fs.rmSync(emptyDir, { recursive: true, force: true });
    }
  });

  it('loads meta + vocab + grammar records', () => {
    const cache = loadEmbeddingsCache(dataDir);
    expect(cache.meta.embed_model).toBe('mock-model');
    expect(cache.vocab).toHaveLength(3);
    expect(cache.grammar).toHaveLength(1);
  });
});

describe('retrievePractice', () => {
  it('rejects a missing/invalid queryVector with a 400', () => {
    try {
      retrievePractice({ queryVector: [] }, dataDir);
      expect.unreachable();
    } catch (err) {
      expect(err).toBeInstanceOf(PracticeRetrieveError);
      expect((err as PracticeRetrieveError).status).toBe(400);
    }
  });

  it('rejects an embedding-dimension mismatch with a 400', () => {
    try {
      retrievePractice({ queryVector: [1, 0, 0] }, dataDir);
      expect.unreachable();
    } catch (err) {
      expect(err).toBeInstanceOf(PracticeRetrieveError);
      expect((err as PracticeRetrieveError).status).toBe(400);
      expect((err as PracticeRetrieveError).message).toMatch(/dimension/);
    }
  });

  it('excludes higher-level vocab and ranks by cosine similarity for the default level', () => {
    const result = retrievePractice({ level: '1A', queryVector: [1, 0], vocabK: 5, grammarM: 5 }, dataDir);
    // v2 (사과) is 1B-only and must not appear when querying level 1A.
    expect(result.hangul).toEqual(['학교', '물']);
  });

  it('includes parent-level vocab when include_levels expands the requested level', () => {
    const result = retrievePractice({ level: '1B', queryVector: [1, 0], vocabK: 5, grammarM: 5 }, dataDir);
    expect(result.hangul).toEqual(['학교', '물', '사과']);
  });

  it('respects vocabK and grammarM limits', () => {
    const result = retrievePractice({ level: '1B', queryVector: [1, 0], vocabK: 1, grammarM: 1 }, dataDir);
    expect(result.hangul).toEqual(['학교']);
    expect(result.grammar).toHaveLength(1);
    expect(result.grammar[0]).toEqual({ id: 'do', form: '-도', english: 'also / even', summary: 'Additive particle.' });
  });

  it('rejects an unknown level with a 400', () => {
    try {
      retrievePractice({ level: '9Z', queryVector: [1, 0] }, dataDir);
      expect.unreachable();
    } catch (err) {
      expect(err).toBeInstanceOf(PracticeRetrieveError);
      expect((err as PracticeRetrieveError).status).toBe(400);
      expect((err as PracticeRetrieveError).message).toMatch(/Unknown level/);
    }
  });

  it('defaults vocabK/grammarM when omitted or non-positive', () => {
    const result = retrievePractice({ level: '1A', queryVector: [1, 0], vocabK: 0, grammarM: -1 }, dataDir);
    expect(result.hangul.length).toBeGreaterThan(0);
    expect(result.grammar.length).toBeGreaterThan(0);
  });
});
