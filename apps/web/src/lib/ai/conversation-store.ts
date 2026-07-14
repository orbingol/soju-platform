import { getItem, removeItem, setItem } from '$lib/storage';

function storageKey(sessionKey: string): string {
  return `ai-conversation:${sessionKey}`;
}

export async function getConversationId(sessionKey: string): Promise<string | null> {
  return getItem<string>(storageKey(sessionKey));
}

export async function saveConversationId(sessionKey: string, conversationId: string): Promise<void> {
  await setItem(storageKey(sessionKey), conversationId);
}

export async function clearConversationId(sessionKey: string): Promise<void> {
  await removeItem(storageKey(sessionKey));
}
