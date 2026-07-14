import { describe, expect, it } from 'vitest';

import { applyTutorName } from './chat';

describe('applyTutorName', () => {
  it('replaces tutor name placeholders', () => {
    expect(applyTutorName('You are {{tutor_name}}.', 'Hee-jae (희재)')).toBe('You are Hee-jae (희재).');
    expect(applyTutorName('Hello {{TUTOR_NAME}}', 'Mina')).toBe('Hello Mina');
  });
});
