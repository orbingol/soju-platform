import { afterEach, describe, expect, it, vi } from 'vitest';

import { aiOfflineMessage, probeAiAvailability } from './availability';

vi.mock('$lib/ai/client', () => ({
  checkAiAvailable: vi.fn(),
}));

import { checkAiAvailable } from '$lib/ai/client';

describe('ai availability', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('probeAiAvailability skips the network when AI is disabled', async () => {
    await expect(probeAiAvailability(false)).resolves.toEqual({ checking: false, available: false });
    expect(checkAiAvailable).not.toHaveBeenCalled();
  });

  it('probeAiAvailability returns checkAiAvailable when enabled', async () => {
    vi.mocked(checkAiAvailable).mockResolvedValue(true);
    await expect(probeAiAvailability(true)).resolves.toEqual({ checking: false, available: true });
    expect(checkAiAvailable).toHaveBeenCalledOnce();
  });

  it('aiOfflineMessage includes feature label and base URL', () => {
    const message = aiOfflineMessage('Practice', 'http://api.test');
    expect(message).toContain('Practice is unavailable at http://api.test');
    expect(message).toContain('Confirm the model service is running');
  });
});
