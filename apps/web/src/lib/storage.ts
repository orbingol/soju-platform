const PREFIX = 'soju-web:';
const LEGACY_PREFIX = 'kr-edu:';

function readRaw(key: string): string | null {
  try {
    return localStorage.getItem(PREFIX + key);
  } catch {
    return null;
  }
}

function writeRaw(key: string, value: string): boolean {
  try {
    localStorage.setItem(PREFIX + key, value);
    return true;
  } catch {
    return false;
  }
}

function migrateLegacyKey(key: string): void {
  try {
    const legacy = localStorage.getItem(LEGACY_PREFIX + key);
    if (legacy === null || readRaw(key) !== null) return;
    writeRaw(key, legacy);
    localStorage.removeItem(LEGACY_PREFIX + key);
  } catch {
    // Ignore migration errors.
  }
}

export function getItem<T = unknown>(key: string): Promise<T | null> {
  return Promise.resolve().then(() => {
    migrateLegacyKey(key);
    const raw = readRaw(key);
    if (raw === null) return null;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return raw as T;
    }
  });
}

export function setItem(key: string, value: unknown): Promise<unknown> {
  return Promise.resolve().then(() => {
    writeRaw(key, JSON.stringify(value));
    return value;
  });
}

export function removeItem(key: string): Promise<void> {
  return Promise.resolve().then(() => {
    try {
      localStorage.removeItem(PREFIX + key);
    } catch {
      // Ignore storage errors.
    }
  });
}
