import { aiTutorName, defaultChatSystemPrompt } from '$lib/config';
import { buildVocabularySummary } from '$lib/data/loader';
import { getItem, removeItem, setItem } from '$lib/storage';

export const GLOBAL_CHAT_SESSION_KEY = 'global-chat';

export function chatTutorLabel(tutorName: string): string {
  return `Chat with ${tutorName}`;
}

const MESSAGES_KEY = 'chat-messages';
const DOCK_OPEN_KEY = 'chat-dock-open';

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

/** Replace {{tutor_name}} (and common variants) with the configured tutor display name. */
export function applyTutorName(template: string, tutorName: string = aiTutorName): string {
  return template.replaceAll('{{tutor_name}}', tutorName).replaceAll('{{TUTOR_NAME}}', tutorName);
}

export function buildChatSystemPrompt(): string {
  const vocabulary = buildVocabularySummary();
  const vocabHint = [...vocabulary.words.slice(0, 20).map((word) => word.hangul), ...vocabulary.verbs.slice(0, 10).map((verb) => verb.hangul)].join(', ');

  const prompt = applyTutorName(defaultChatSystemPrompt);
  return `${prompt}\n\nKnown vocabulary includes: ${vocabHint}`;
}

export async function loadChatMessages(): Promise<ChatTurn[]> {
  const stored = await getItem<ChatTurn[]>(MESSAGES_KEY);
  if (!Array.isArray(stored)) return [];
  return stored.filter((message) => (message.role === 'user' || message.role === 'assistant') && typeof message.content === 'string');
}

export async function saveChatMessages(messages: ChatTurn[]): Promise<void> {
  await setItem(MESSAGES_KEY, messages);
}

export async function clearChatMessages(): Promise<void> {
  await removeItem(MESSAGES_KEY);
}

export async function loadChatDockOpen(): Promise<boolean> {
  const stored = await getItem<boolean>(DOCK_OPEN_KEY);
  return stored === true;
}

export async function saveChatDockOpen(open: boolean): Promise<void> {
  await setItem(DOCK_OPEN_KEY, open);
}

export function openChatDock(): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent('soju:chat-open'));
}
