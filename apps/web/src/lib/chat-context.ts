import type { AiCompletionRequest, AiMessage } from '$lib/ai/types';
import type { ChatTurn } from '$lib/chat';
import { chatKeepRecent, chatSummaryTrigger } from '$lib/config';
import { getItem, removeItem, setItem } from '$lib/storage';

const MEMORY_KEY = 'chat-memory';

export interface ChatMemory {
  summary: string;
  /** Number of leading turns folded into `summary`. */
  summarizedCount: number;
}

export interface ChatContextThresholds {
  trigger: number;
  keepRecent: number;
}

type CompleteFn = (request: AiCompletionRequest) => Promise<string>;

const SUMMARIZE_SYSTEM = [
  'You compress a Korean tutoring chat into a short memory note for the teacher AI.',
  'Preserve: topics the student asked about, grammar forms, Korean+English examples, student goals/focus, open questions.',
  'Omit: greetings, encouragement fluff, repeated explanations.',
  'Max ~12 short bullet lines. Plain text only (use "-" bullets). No markdown headings.',
].join(' ');

function defaultThresholds(): ChatContextThresholds {
  return { trigger: chatSummaryTrigger, keepRecent: chatKeepRecent };
}

export function needsSummarization(messageCount: number, memory: ChatMemory | null, thresholds: ChatContextThresholds = defaultThresholds()): boolean {
  const { trigger, keepRecent } = thresholds;
  if (messageCount <= trigger) return false;
  const needCoverUntil = messageCount - keepRecent;
  if (needCoverUntil <= 0) return false;
  if (!memory?.summary) return true;
  return memory.summarizedCount < needCoverUntil;
}

function formatTurnsForSummary(turns: ChatTurn[]): string {
  return turns.map((turn) => `${turn.role === 'user' ? 'Student' : 'Teacher'}: ${turn.content}`).join('\n\n');
}

export async function loadChatMemory(): Promise<ChatMemory | null> {
  const stored = await getItem<ChatMemory>(MEMORY_KEY);
  if (!stored || typeof stored !== 'object') return null;
  if (typeof stored.summary !== 'string' || typeof stored.summarizedCount !== 'number') return null;
  if (stored.summarizedCount < 0) return null;
  return stored;
}

export async function saveChatMemory(memory: ChatMemory): Promise<void> {
  await setItem(MEMORY_KEY, memory);
}

export async function clearChatMemory(): Promise<void> {
  await removeItem(MEMORY_KEY);
}

export function buildModelMessages(systemPrompt: string, messages: ChatTurn[], memory: ChatMemory | null, thresholds: ChatContextThresholds = defaultThresholds()): AiMessage[] {
  const { trigger, keepRecent } = thresholds;
  const system: AiMessage = { role: 'system', content: systemPrompt };

  if (messages.length <= trigger) {
    return [system, ...messages.map((message) => ({ role: message.role, content: message.content }))];
  }

  if (memory?.summary && memory.summarizedCount > 0) {
    const start = Math.min(memory.summarizedCount, Math.max(0, messages.length - keepRecent));
    return [
      system,
      {
        role: 'system',
        content: `Lesson memory (continue from this):\n${memory.summary}`,
      },
      ...messages.slice(start).map((message) => ({ role: message.role, content: message.content })),
    ];
  }

  // Soft-fail / no summary yet: keep only the recent window.
  return [system, ...messages.slice(-keepRecent).map((message) => ({ role: message.role, content: message.content }))];
}

async function summarizeTurns(previousSummary: string | null, turns: ChatTurn[], model: string, complete: CompleteFn): Promise<string> {
  const userContent = previousSummary
    ? ['Previous lesson memory:', previousSummary, '', 'New turns to fold in:', formatTurnsForSummary(turns), '', 'Update the lesson memory.'].join('\n')
    : ['Chat turns to summarize:', formatTurnsForSummary(turns), '', 'Write the lesson memory.'].join('\n');

  const text = await complete({
    model,
    messages: [
      { role: 'system', content: SUMMARIZE_SYSTEM },
      { role: 'user', content: userContent },
    ],
    temperature: 0.2,
  });

  return text.trim();
}

/**
 * Ensure older turns are folded into lesson memory when the transcript is long.
 * Does not take a sessionKey so Conversations-mode state is not polluted.
 */
export async function ensureChatMemory(options: {
  messages: ChatTurn[];
  model: string;
  memory: ChatMemory | null;
  complete: CompleteFn;
  thresholds?: ChatContextThresholds;
}): Promise<{ memory: ChatMemory | null; didSummarize: boolean }> {
  const thresholds = options.thresholds ?? defaultThresholds();
  const { trigger, keepRecent } = thresholds;
  const { messages, model, complete } = options;
  let memory = options.memory;

  if (messages.length <= trigger) {
    return { memory, didSummarize: false };
  }

  const needCoverUntil = messages.length - keepRecent;
  if (needCoverUntil <= 0) {
    return { memory, didSummarize: false };
  }

  if (memory?.summary && memory.summarizedCount >= needCoverUntil) {
    return { memory, didSummarize: false };
  }

  const from = memory?.summarizedCount ?? 0;
  const toFold = messages.slice(from, needCoverUntil);
  if (toFold.length === 0) {
    return { memory, didSummarize: false };
  }

  try {
    const summary = await summarizeTurns(memory?.summary ?? null, toFold, model, complete);
    if (!summary) {
      return { memory, didSummarize: false };
    }
    memory = { summary, summarizedCount: needCoverUntil };
    await saveChatMemory(memory);
    return { memory, didSummarize: true };
  } catch {
    // Soft-fail: caller will send recent turns only via buildModelMessages.
    return { memory, didSummarize: false };
  }
}
