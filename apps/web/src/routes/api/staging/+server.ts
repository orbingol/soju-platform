import { json } from '@sveltejs/kit';
import fs from 'node:fs';
import path from 'node:path';
import yaml from 'yaml';

import { dev } from '$app/environment';

import { getDataDir, stagingDir } from '$lib/data/paths';

export const prerender = false;

type StagingKind = 'exercises' | 'stories' | 'vocabulary';

const KIND_DIRS: Record<StagingKind, string> = {
  exercises: 'exercises',
  stories: 'stories',
  vocabulary: '',
};

const KIND_FILES: Record<StagingKind, (date: string) => string> = {
  exercises: (date) => `${date}.yaml`,
  stories: (date) => `${date}.yaml`,
  vocabulary: () => 'vocabulary-candidates.yaml',
};

export async function POST({ request }) {
  if (!dev) {
    return json({ error: 'Staging API is dev-only' }, { status: 403 });
  }

  let body: { kind?: StagingKind; payload?: unknown; date?: string };
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const kind = body.kind;
  if (!kind || !(kind in KIND_DIRS)) {
    return json({ error: 'kind must be exercises, stories, or vocabulary' }, { status: 400 });
  }

  if (!body.payload || typeof body.payload !== 'object') {
    return json({ error: 'payload object is required' }, { status: 400 });
  }

  const date = body.date ?? new Date().toISOString().slice(0, 10);
  const stagingRoot = stagingDir(getDataDir());
  const subdir = KIND_DIRS[kind];
  const targetDir = subdir ? path.join(stagingRoot, subdir) : stagingRoot;
  const filename = KIND_FILES[kind](date);
  const targetPath = path.join(targetDir, filename);

  fs.mkdirSync(targetDir, { recursive: true });
  const yamlText = yaml.stringify(body.payload);
  fs.writeFileSync(targetPath, yamlText, 'utf8');

  return json({
    ok: true,
    path: subdir ? `data/staging/${subdir}/${filename}` : `data/staging/${filename}`,
  });
}
