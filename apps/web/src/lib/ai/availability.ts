import { checkAiAvailable } from '$lib/ai/client';
import { sojuApiBaseUrl } from '$lib/config';

export type AiAvailabilityState = { checking: boolean; available: boolean };

/** Probe whether the Soju AI API is reachable when the feature is enabled. */
export async function probeAiAvailability(aiEnabled: boolean): Promise<AiAvailabilityState> {
  if (!aiEnabled) return { checking: false, available: false };
  return { checking: false, available: await checkAiAvailable() };
}

/** Shared offline copy for Chat dock and feature gates. */
export function aiOfflineMessage(featureLabel: string, baseUrl: string = sojuApiBaseUrl): string {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'this site';
  return `${featureLabel} is unavailable at ${baseUrl}. Confirm the model service is running, CORS allows ${origin}, then reload.`;
}
