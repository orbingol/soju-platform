import { aiModel } from '$lib/config';

import { AI_FETCH_TIMEOUT_MS, apiUrl, checkServerAvailable, fetchWithTimeout, readError } from './http';
import { extractChatCompletionText } from './messages';
import { parseChatCompletionDelta, readSseDataLines } from './sse';
import type { AiClient, AiCompletionRequest } from './types';

function buildBody(request: AiCompletionRequest) {
  return {
    model: request.model ?? aiModel,
    messages: request.messages,
    stream: request.stream ?? false,
    ...(request.jsonMode ? { format: 'json' } : {}),
    temperature: request.temperature ?? 0.7,
  };
}

function requestInit(body: unknown, signal?: AbortSignal): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    ...(signal ? { signal } : {}),
  };
}

export const chatCompletionsClient: AiClient = {
  checkAvailable: checkServerAvailable,

  async complete(request) {
    const response = await fetchWithTimeout(
      apiUrl('/v1/chat/completions'),
      requestInit({ ...buildBody(request), stream: false }, request.signal),
      AI_FETCH_TIMEOUT_MS,
    );

    if (!response.ok) {
      throw new Error(await readError(response));
    }

    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    return extractChatCompletionText(payload);
  },

  async *stream(request) {
    const response = await fetchWithTimeout(
      apiUrl('/v1/chat/completions'),
      requestInit({ ...buildBody(request), stream: true }, request.signal),
      AI_FETCH_TIMEOUT_MS,
    );

    if (!response.ok) {
      throw new Error(await readError(response));
    }

    if (!response.body) {
      throw new Error('Stream returned no body');
    }

    for await (const payload of readSseDataLines(response.body)) {
      const token = parseChatCompletionDelta(payload);
      if (token) yield token;
    }
  },
};
