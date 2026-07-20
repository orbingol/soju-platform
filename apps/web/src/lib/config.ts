import { env as dynamicPublicEnv } from '$env/dynamic/public';
import {
  PUBLIC_AI_API_MODE,
  PUBLIC_AI_BASE_URL,
  PUBLIC_AI_EMBED_MODEL,
  PUBLIC_AI_ENABLED,
  PUBLIC_AI_MODEL,
  PUBLIC_AI_SYSTEM_PROMPT,
  PUBLIC_AI_TUTOR_NAME,
} from '$env/static/public';

export type AiApiMode = 'chat-completions' | 'conversations';
export type TtsEngine = 'piper' | 'browser';

function firstDefined(...values: Array<string | undefined>): string | undefined {
  for (const value of values) {
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return undefined;
}

function parsePositiveInt(raw: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(raw ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

/** Clamp chat compaction thresholds so keepRecent >= 2 and trigger > keepRecent. */
export function resolveChatContextThresholds(triggerRaw?: string, keepRaw?: string): { trigger: number; keepRecent: number } {
  const keepRecent = Math.max(2, parsePositiveInt(keepRaw, 6));
  let trigger = parsePositiveInt(triggerRaw, 10);
  if (trigger <= keepRecent) {
    trigger = keepRecent + 1;
  }
  return { trigger, keepRecent };
}

export function resolveTtsEngine(raw?: string): TtsEngine {
  return raw?.trim().toLowerCase() === 'browser' ? 'browser' : 'piper';
}

/** When true, Practice and Chat are available (requires a running language model at runtime). */
export const aiEnabled = firstDefined(PUBLIC_AI_ENABLED, dynamicPublicEnv.PUBLIC_OLLAMA_ENABLED) === 'true';

export const aiBaseUrl = (firstDefined(PUBLIC_AI_BASE_URL, dynamicPublicEnv.PUBLIC_OLLAMA_BASE_URL) ?? 'http://localhost:11434').replace(/\/$/, '');

export const aiModel = firstDefined(PUBLIC_AI_MODEL, dynamicPublicEnv.PUBLIC_OLLAMA_MODEL) ?? 'gemma4:e4b';

/** Ollama embedding model for Practice's browser-side theme embedding (must match `soju embed-index`). */
export const aiEmbedModel = firstDefined(PUBLIC_AI_EMBED_MODEL, dynamicPublicEnv.PUBLIC_OLLAMA_EMBED_MODEL) ?? 'nomic-embed-text';

export const aiApiMode: AiApiMode = firstDefined(PUBLIC_AI_API_MODE) === 'conversations' ? 'conversations' : 'chat-completions';

export const defaultChatTutorName = 'Hee-jae (희재)';

export const aiTutorName = firstDefined(PUBLIC_AI_TUTOR_NAME) ?? defaultChatTutorName;

export const defaultChatSystemPrompt =
  firstDefined(PUBLIC_AI_SYSTEM_PROMPT, dynamicPublicEnv.PUBLIC_OLLAMA_SYSTEM_PROMPT) ||
  [
    'You are {{tutor_name}}, a friendly Korean language teacher for beginners.',
    'Keep replies short (2–4 sentences). If the question is vague, ask one clarifying question first.',
    'Once the topic is clear, give a brief explanation and at most one example (Korean + English).',
    'Be warm and patient with light empathy; a gentle emoji is fine when it fits—keep encouragement brief.',
    'Prefer Soju vocabulary when helpful. Mix Korean and English naturally.',
    'Use plain text; **bold** for key Korean forms is fine. Write → for conjugation; avoid LaTeX and ---.',
  ].join(' ');

const chatThresholds = resolveChatContextThresholds(dynamicPublicEnv.PUBLIC_AI_CHAT_SUMMARY_TRIGGER, dynamicPublicEnv.PUBLIC_AI_CHAT_KEEP_RECENT);

/** Summarize when chat turn count exceeds this value. */
export const chatSummaryTrigger = chatThresholds.trigger;

/** Recent turns kept verbatim after summarization. */
export const chatKeepRecent = chatThresholds.keepRecent;

/** Default TTS engine from env (user can override in Settings). */
export const defaultTtsEngine = resolveTtsEngine(dynamicPublicEnv.PUBLIC_TTS_ENGINE);

/** Browser-reachable Piper HTTP root. */
export const piperBaseUrl = (firstDefined(dynamicPublicEnv.PUBLIC_TTS_PIPER_BASE_URL) ?? 'http://localhost:5500').replace(/\/$/, '');

/** Piper / Edge voice name for /v1/audio/speech. */
export const piperVoice = firstDefined(dynamicPublicEnv.PUBLIC_TTS_PIPER_VOICE) ?? 'ko-KR-SunHiNeural';
