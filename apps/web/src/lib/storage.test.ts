import { beforeEach, describe, expect, it, vi } from 'vitest';

import { getItem, removeItem, setItem } from './storage';

describe('storage', () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    });
  });

  it('round-trips JSON values under the soju-web prefix', async () => {
    await setItem('demo', { ok: true });
    expect(store.get('soju-web:demo')).toBe('{"ok":true}');
    await expect(getItem('demo')).resolves.toEqual({ ok: true });
    await removeItem('demo');
    await expect(getItem('demo')).resolves.toBeNull();
  });

  it('migrates legacy kr-edu keys on read', async () => {
    store.set('kr-edu:legacy', JSON.stringify({ migrated: true }));
    await expect(getItem('legacy')).resolves.toEqual({ migrated: true });
    expect(store.has('soju-web:legacy')).toBe(true);
    expect(store.has('kr-edu:legacy')).toBe(false);
  });
});
