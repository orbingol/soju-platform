import path from 'node:path';

/** Safe URL/path segment for topic ids, type slugs, and similar params. */
export const SLUG_PATTERN = /^[a-z0-9_-]+$/;

export function getDataDir(): string {
  const fromEnv = process.env.DATA_DIR;
  if (fromEnv) return fromEnv;
  return path.resolve(process.cwd(), '../../data');
}

export function contentDir(root: string): string {
  return path.join(root, 'content');
}

export function registryDir(root: string): string {
  return path.join(contentDir(root), 'registry');
}

export function verbsDir(root: string): string {
  return path.join(contentDir(root), 'verbs');
}

export function topicsDir(root: string): string {
  return path.join(contentDir(root), 'topics');
}

export function grammarDir(root: string): string {
  return path.join(contentDir(root), 'grammar');
}

export function practiceDir(root: string): string {
  return path.join(contentDir(root), 'practice');
}

export function stagingDir(root: string): string {
  return path.join(root, 'staging');
}

export function assertSafeSlug(slug: string, label = 'slug'): void {
  if (!SLUG_PATTERN.test(slug)) {
    throw new Error(`Invalid ${label}`);
  }
}

/**
 * Resolve `parts` under `baseDir` and ensure the result stays inside that base.
 * Throws a domain error (no absolute paths) if the join escapes.
 */
export function resolveUnder(baseDir: string, ...parts: string[]): string {
  const base = path.resolve(baseDir);
  const resolved = path.resolve(base, ...parts);
  if (resolved !== base && !resolved.startsWith(base + path.sep)) {
    throw new Error('Path escapes content directory');
  }
  return resolved;
}

/** Relative path for error messages (never absolute). */
export function displayDataPath(filePath: string, dataDir: string): string {
  const rel = path.relative(path.resolve(dataDir), path.resolve(filePath));
  if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) {
    return rel.split(path.sep).join('/');
  }
  return path.basename(filePath);
}
