import { getItem, setItem } from '$lib/storage';

const THEME_KEY = 'theme';
export type ThemeMode = 'auto' | 'light' | 'dark';

export function applyTheme(theme: ThemeMode): void {
  const root = document.documentElement;
  if (theme === 'auto') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', theme);
  }
  root.dataset.themeMode = theme;
}

export async function loadTheme(): Promise<ThemeMode> {
  const stored = await getItem<ThemeMode>(THEME_KEY);
  const theme = stored ?? 'auto';
  applyTheme(theme);
  return theme;
}

export async function saveTheme(theme: ThemeMode): Promise<void> {
  applyTheme(theme);
  await setItem(THEME_KEY, theme);
}

export function themeFlashScript(): string {
  return `(function(){try{var k='soju-web:theme';var r=localStorage.getItem(k);if(r===null)r=localStorage.getItem('kr-edu:theme');if(!r)return;var v=JSON.parse(r);if(v==='light'||v==='dark')document.documentElement.setAttribute('data-theme',v);}catch(e){}})();`;
}
