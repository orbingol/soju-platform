import { describe, expect, it } from 'vitest';

import { parseChatCompletionDelta, parseResponsesStreamDelta } from './sse';

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
