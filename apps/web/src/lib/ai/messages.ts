import type { AiMessage } from './types';

export function splitPrompt(messages: AiMessage[]): { instructions?: string; latestUser?: string } {
  const instructions = messages.find((message) => message.role === 'system')?.content;
  const userMessages = messages.filter((message) => message.role === 'user');
  const latestUser = userMessages.at(-1)?.content;

  return { instructions, latestUser };
}

export function extractChatCompletionText(payload: { choices?: Array<{ message?: { content?: string } }> }): string {
  return payload.choices?.[0]?.message?.content?.trim() ?? '';
}

export function extractResponsesText(payload: {
  output_text?: string;
  output?: Array<{
    type?: string;
    content?: Array<{ type?: string; text?: string }>;
  }>;
}): string {
  if (typeof payload.output_text === 'string' && payload.output_text.trim()) {
    return payload.output_text.trim();
  }

  for (const item of payload.output ?? []) {
    if (item.type !== 'message') continue;
    for (const part of item.content ?? []) {
      if ((part.type === 'output_text' || part.type === 'text') && part.text?.trim()) {
        return part.text.trim();
      }
    }
  }

  return '';
}
