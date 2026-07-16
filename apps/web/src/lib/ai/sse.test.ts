import { describe, expect, it } from 'vitest';

import { parseChatCompletionDelta, parseResponsesStreamDelta, readSseDataLines } from './sse';

function streamFrom(text: string): ReadableStream<Uint8Array> {
  const bytes = new TextEncoder().encode(text);
  return new ReadableStream({
    start(controller) {
      controller.enqueue(bytes);
      controller.close();
    },
  });
}

describe('sse parsers', () => {
  it('parses chat completion deltas', () => {
    expect(parseChatCompletionDelta('{"choices":[{"delta":{"content":"안녕"}}]}')).toBe('안녕');
    expect(parseChatCompletionDelta('not-json')).toBeNull();
  });

  it('parses responses stream deltas', () => {
    expect(parseResponsesStreamDelta(JSON.stringify({ type: 'response.output_text.delta', delta: 'hello' }))).toBe('hello');
    expect(parseResponsesStreamDelta(JSON.stringify({ output_text: 'full' }))).toBe('full');
  });
});

describe('readSseDataLines', () => {
  it('yields data lines separated by newlines', async () => {
    const chunks: string[] = [];
    for await (const line of readSseDataLines(streamFrom('data: {"a":1}\ndata: {"b":2}\n'))) {
      chunks.push(line);
    }
    expect(chunks).toEqual(['{"a":1}', '{"b":2}']);
  });

  it('flushes a trailing data line when the stream ends without a final newline', async () => {
    const chunks: string[] = [];
    for await (const line of readSseDataLines(streamFrom('data: {"tail":true}'))) {
      chunks.push(line);
    }
    expect(chunks).toEqual(['{"tail":true}']);
  });

  it('skips [DONE] and empty data lines', async () => {
    const chunks: string[] = [];
    for await (const line of readSseDataLines(streamFrom('data: hi\ndata: [DONE]\ndata: \n'))) {
      chunks.push(line);
    }
    expect(chunks).toEqual(['hi']);
  });
});
