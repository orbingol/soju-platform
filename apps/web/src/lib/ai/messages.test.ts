import { describe, expect, it } from 'vitest';

import { extractChatCompletionText, extractResponsesText, splitPrompt } from './messages';
import { parseChatCompletionDelta, parseResponsesStreamDelta } from './sse';

describe('ai messages', () => {
  it('splits system instructions from the latest user turn', () => {
    expect(
      splitPrompt([
        { role: 'system', content: 'Teach Korean' },
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: '안녕하세요' },
        { role: 'user', content: 'How do I say thanks?' },
      ]),
    ).toEqual({
      instructions: 'Teach Korean',
      latestUser: 'How do I say thanks?',
    });
  });

  it('extracts chat completion and responses payloads', () => {
    expect(
      extractChatCompletionText({
        choices: [{ message: { content: '  hello  ' } }],
      }),
    ).toBe('hello');

    expect(
      extractResponsesText({
        output_text: 'json-body',
      }),
    ).toBe('json-body');

    expect(
      extractResponsesText({
        output: [
          {
            type: 'message',
            content: [{ type: 'output_text', text: 'from output array' }],
          },
        ],
      }),
    ).toBe('from output array');
  });
});

describe('ai sse', () => {
  it('parses chat completion stream deltas', () => {
    expect(parseChatCompletionDelta('{"choices":[{"delta":{"content":"안"}}]}')).toBe('안');
  });

  it('parses responses stream deltas', () => {
    expect(parseResponsesStreamDelta('{"type":"response.output_text.delta","delta":"녕"}')).toBe('녕');
  });
});
