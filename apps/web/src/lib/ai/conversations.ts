import { aiModel } from '$lib/config';

import { clearConversationId, getConversationId, saveConversationId } from './conversation-store';
import { AI_FETCH_TIMEOUT_MS, apiUrl, checkServerAvailable, fetchWithTimeout, readError } from './http';
import { extractResponsesText, splitPrompt } from './messages';
import { parseResponsesStreamDelta, readSseDataLines } from './sse';
import type { AiClient, AiCompletionRequest } from './types';

function buildInput(request: AiCompletionRequest, latestUser: string) {
  if (request.sessionKey) {
    return latestUser;
  }

  return request.messages
    .filter((message) => message.role !== 'system')
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
}

function buildBody(request: AiCompletionRequest, conversationId?: string | null) {
  const { instructions, latestUser } = splitPrompt(request.messages);
  if (!latestUser) {
    throw new Error('At least one user message is required');
  }

  const body: Record<string, unknown> = {
    model: request.model ?? aiModel,
    input: buildInput(request, latestUser),
    stream: request.stream ?? false,
    temperature: request.temperature ?? 0.7,
  };

  if (instructions) {
    body.instructions = instructions;
  }

  if (conversationId) {
    body.conversation = conversationId;
  }

  if (request.jsonMode) {
    body.text = { format: { type: 'json_object' } };
  }

  if (request.maxTokens) {
    body.max_output_tokens = request.maxTokens;
  }

  return body;
}

async function createConversation(signal?: AbortSignal): Promise<string> {
  const response = await fetchWithTimeout(
    apiUrl('/v1/conversations'),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
      ...(signal ? { signal } : {}),
    },
    AI_FETCH_TIMEOUT_MS,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = (await response.json()) as { id?: string };
  if (!payload.id) {
    throw new Error('Conversation create response missing id');
  }

  return payload.id;
}

async function ensureConversation(sessionKey: string, signal?: AbortSignal): Promise<string> {
  const existing = await getConversationId(sessionKey);
  if (existing) return existing;

  const conversationId = await createConversation(signal);
  await saveConversationId(sessionKey, conversationId);
  return conversationId;
}

async function resolveConversationId(request: AiCompletionRequest): Promise<string | null> {
  if (!request.sessionKey) return null;
  return ensureConversation(request.sessionKey, request.signal);
}

export const conversationsClient: AiClient = {
  checkAvailable: checkServerAvailable,

  async complete(request) {
    const conversationId = await resolveConversationId(request);
    const response = await fetchWithTimeout(
      apiUrl('/v1/responses'),
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...buildBody(request, conversationId), stream: false }),
        ...(request.signal ? { signal: request.signal } : {}),
      },
      request.timeoutMs ?? AI_FETCH_TIMEOUT_MS,
    );

    if (!response.ok) {
      if (conversationId && request.sessionKey) {
        await clearConversationId(request.sessionKey);
      }
      throw new Error(await readError(response));
    }

    const payload = (await response.json()) as {
      output_text?: string;
      output?: Array<{
        type?: string;
        content?: Array<{ type?: string; text?: string }>;
      }>;
    };

    return extractResponsesText(payload);
  },

  async *stream(request) {
    const conversationId = await resolveConversationId(request);
    const response = await fetchWithTimeout(
      apiUrl('/v1/responses'),
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...buildBody(request, conversationId), stream: true }),
        ...(request.signal ? { signal: request.signal } : {}),
      },
      request.timeoutMs ?? AI_FETCH_TIMEOUT_MS,
    );

    if (!response.ok) {
      if (conversationId && request.sessionKey) {
        await clearConversationId(request.sessionKey);
      }
      throw new Error(await readError(response));
    }

    if (!response.body) {
      throw new Error('Stream returned no body');
    }

    for await (const payload of readSseDataLines(response.body)) {
      const token = parseResponsesStreamDelta(payload);
      if (token) yield token;
    }
  },
};
