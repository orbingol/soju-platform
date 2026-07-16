export async function* readSseDataLines(body: ReadableStream<Uint8Array>): AsyncGenerator<string, void, unknown> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const flushLine = function* (line: string): Generator<string, void, unknown> {
    const trimmed = line.trim();
    if (!trimmed.startsWith('data:')) return;

    const data = trimmed.slice(5).trim();
    if (!data || data === '[DONE]') return;
    yield data;
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      buffer += decoder.decode();
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      yield* flushLine(line);
    }
  }

  // Stream ended without a trailing newline — flush any leftover `data:` line.
  if (buffer.length > 0) {
    yield* flushLine(buffer);
  }
}

export function parseChatCompletionDelta(payload: string): string | null {
  try {
    const chunk = JSON.parse(payload) as {
      choices?: Array<{ delta?: { content?: string } }>;
    };
    return chunk.choices?.[0]?.delta?.content ?? null;
  } catch {
    return null;
  }
}

export function parseResponsesStreamDelta(payload: string): string | null {
  try {
    const chunk = JSON.parse(payload) as {
      type?: string;
      delta?: string;
      response?: { output_text?: string };
      output_text?: string;
    };

    if (chunk.type === 'response.output_text.delta' && typeof chunk.delta === 'string') {
      return chunk.delta;
    }

    if (typeof chunk.output_text === 'string' && chunk.output_text.length > 0) {
      return chunk.output_text;
    }

    if (typeof chunk.response?.output_text === 'string' && chunk.response.output_text.length > 0) {
      return chunk.response.output_text;
    }

    return parseChatCompletionDelta(payload);
  } catch {
    return null;
  }
}
