import path from 'node:path';

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

export function stagingDir(root: string): string {
  return path.join(root, 'staging');
}
