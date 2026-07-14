import { aiApiMode } from '$lib/config';

import { chatCompletionsClient } from './chat-completions';
import { conversationsClient } from './conversations';
import type { AiClient, AiCompletionRequest, AiMessage } from './types';

export type { AiClient, AiCompletionRequest, AiMessage };

function getClient(): AiClient {
  return aiApiMode === 'conversations' ? conversationsClient : chatCompletionsClient;
}

export async function checkAiAvailable(): Promise<boolean> {
  return getClient().checkAvailable();
}

export async function complete(request: AiCompletionRequest): Promise<string> {
  return getClient().complete(request);
}

export async function* streamCompletion(request: AiCompletionRequest): AsyncGenerator<string, void, unknown> {
  yield* getClient().stream(request);
}

export function getAiClient(): AiClient {
  return getClient();
}
