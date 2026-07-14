import { aiModel } from '$lib/config';

import { apiUrl, checkServerAvailable, readError } from './http';
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

export const chatCompletionsClient: AiClient = {
  checkAvailable: checkServerAvailable,

  async complete(request) {
    const response = await fetch(apiUrl('/v1/chat/completions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...buildBody(request), stream: false }),
    });

    if (!response.ok) {
      throw new Error(await readError(response));
    }

    const payload = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    return extractChatCompletionText(payload);
  },

  async *stream(request) {
    const response = await fetch(apiUrl('/v1/chat/completions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...buildBody(request), stream: true }),
    });

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
