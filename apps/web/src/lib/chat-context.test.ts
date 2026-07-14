import { describe, expect, it, vi } from 'vitest';

import { buildModelMessages, ensureChatMemory, needsSummarization, type ChatMemory } from './chat-context';
import type { ChatTurn } from './chat';
import { resolveChatContextThresholds } from './config';

function turns(count: number): ChatTurn[] {
  return Array.from({ length: count }, (_, index) => ({
    role: index % 2 === 0 ? 'user' : 'assistant',
    content: `msg-${index}`,
  }));
}

const thresholds = { trigger: 10, keepRecent: 6 };

describe('resolveChatContextThresholds', () => {
  it('uses defaults and clamps keep/trigger', () => {
    expect(resolveChatContextThresholds(undefined, undefined)).toEqual({
      trigger: 10,
      keepRecent: 6,
    });
    expect(resolveChatContextThresholds('4', '8')).toEqual({
      trigger: 9,
      keepRecent: 8,
    });
    expect(resolveChatContextThresholds('3', '1')).toEqual({
      trigger: 3,
      keepRecent: 2,
    });
  });
});

describe('needsSummarization', () => {
  it('is false while under the trigger', () => {
    expect(needsSummarization(10, null, thresholds)).toBe(false);
    expect(needsSummarization(6, null, thresholds)).toBe(false);
  });

  it('is true when over trigger with no memory', () => {
    expect(needsSummarization(11, null, thresholds)).toBe(true);
  });

  it('is false when memory already covers the aged-out prefix', () => {
    const memory: ChatMemory = { summary: '- past tense', summarizedCount: 5 };
    expect(needsSummarization(11, memory, thresholds)).toBe(false);
  });

  it('is true when memory is behind the needed prefix', () => {
    const memory: ChatMemory = { summary: '- past tense', summarizedCount: 2 };
    expect(needsSummarization(12, memory, thresholds)).toBe(true);
  });
});

describe('buildModelMessages', () => {
  it('sends the full transcript under the trigger', () => {
    const messages = turns(8);
    const built = buildModelMessages('Teach Korean', messages, null, thresholds);
    expect(built).toHaveLength(9);
    expect(built[0]).toEqual({ role: 'system', content: 'Teach Korean' });
    expect(built[1]?.content).toBe('msg-0');
  });

  it('injects lesson memory and recent turns when compacted', () => {
    const messages = turns(12);
    const memory: ChatMemory = { summary: '- focus: past tense', summarizedCount: 6 };
    const built = buildModelMessages('Teach Korean', messages, memory, thresholds);
    expect(built[0]?.content).toBe('Teach Korean');
    expect(built[1]).toEqual({
      role: 'system',
      content: 'Lesson memory (continue from this):\n- focus: past tense',
    });
    expect(built.slice(2).map((message) => message.content)).toEqual(['msg-6', 'msg-7', 'msg-8', 'msg-9', 'msg-10', 'msg-11']);
  });

  it('falls back to recent turns only when over trigger without summary', () => {
    const messages = turns(12);
    const built = buildModelMessages('Teach Korean', messages, null, thresholds);
    expect(built).toHaveLength(7);
    expect(built.slice(1).map((message) => message.content)).toEqual(['msg-6', 'msg-7', 'msg-8', 'msg-9', 'msg-10', 'msg-11']);
  });
});

describe('ensureChatMemory', () => {
  it('summarizes newly aged-out turns and updates memory', async () => {
    const messages = turns(12);
    const complete = vi.fn().mockResolvedValue('- topics: past tense\n- example: 갔어요');

    const result = await ensureChatMemory({
      messages,
      model: 'test-model',
      memory: null,
      complete,
      thresholds,
    });

    expect(result.didSummarize).toBe(true);
    expect(result.memory).toEqual({
      summary: '- topics: past tense\n- example: 갔어요',
      summarizedCount: 6,
    });
    expect(complete).toHaveBeenCalledOnce();
    const request = complete.mock.calls[0]?.[0];
    expect(request.model).toBe('test-model');
    expect(request.sessionKey).toBeUndefined();
    expect(request.messages[0]?.role).toBe('system');
  });

  it('skips the model when memory is already current', async () => {
    const messages = turns(12);
    const complete = vi.fn();
    const memory: ChatMemory = { summary: '- already done', summarizedCount: 6 };

    const result = await ensureChatMemory({
      messages,
      model: 'test-model',
      memory,
      complete,
      thresholds,
    });

    expect(result.didSummarize).toBe(false);
    expect(result.memory).toEqual(memory);
    expect(complete).not.toHaveBeenCalled();
  });

  it('soft-fails and keeps prior memory when summarize throws', async () => {
    const messages = turns(12);
    const complete = vi.fn().mockRejectedValue(new Error('offline'));
    const memory: ChatMemory = { summary: '- prior', summarizedCount: 2 };

    const result = await ensureChatMemory({
      messages,
      model: 'test-model',
      memory,
      complete,
      thresholds,
    });

    expect(result.didSummarize).toBe(false);
    expect(result.memory).toEqual(memory);
  });
});
