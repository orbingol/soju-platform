import { describe, expect, it } from 'vitest';

import { themeFlashScript } from './theme';

describe('theme helpers', () => {
  it('emits a flash script that reads soju-web theme storage', () => {
    const script = themeFlashScript();
    expect(script).toContain('soju-web:theme');
    expect(script).toContain('data-theme');
  });
});
