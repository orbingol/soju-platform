import { env as dynamicPublicEnv } from '$env/dynamic/public';
import { PUBLIC_AI_BASE_URL, PUBLIC_AI_ENABLED } from '$env/static/public';

export type AiApiMode = 'chat-completions' | 'conversations';
export type TtsEngine = 'local' | 'browser';

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

/** Resolve TTS engine; ``piper`` is accepted as a legacy alias for ``local``. */
export function resolveTtsEngine(raw?: string): TtsEngine {
  const normalized = raw?.trim().toLowerCase();
  if (normalized === 'browser') return 'browser';
  return 'local';
}

/** When true, Practice and Chat are available (requires Soju backend + LLM at runtime). */
export const aiEnabled = firstDefined(PUBLIC_AI_ENABLED, dynamicPublicEnv.PUBLIC_OLLAMA_ENABLED) === 'true';

/** Browser-reachable Soju API root (nginx → FastAPI in prod). */
export const sojuApiBaseUrl = (
  firstDefined(PUBLIC_AI_BASE_URL, dynamicPublicEnv.PUBLIC_OLLAMA_BASE_URL, dynamicPublicEnv.PUBLIC_TTS_PIPER_BASE_URL) ??
  'http://localhost:8080'
).replace(/\/$/, '');

/** @deprecated Prefer ``sojuApiBaseUrl`` — same origin for OpenAI-compatible AI routes. */
export const aiBaseUrl = sojuApiBaseUrl;

/** Local TTS HTTP root (same Soju API as AI). */
export const localTtsBaseUrl = (
  firstDefined(dynamicPublicEnv.PUBLIC_TTS_PIPER_BASE_URL, PUBLIC_AI_BASE_URL) ?? sojuApiBaseUrl
).replace(/\/$/, '');

const envChatThresholds = resolveChatContextThresholds(
  dynamicPublicEnv.PUBLIC_AI_CHAT_SUMMARY_TRIGGER,
  dynamicPublicEnv.PUBLIC_AI_CHAT_KEEP_RECENT,
);

export const defaultChatTutorName = 'Hee-jae (희재)';

const envSystemPrompt =
  firstDefined(dynamicPublicEnv.PUBLIC_AI_SYSTEM_PROMPT, dynamicPublicEnv.PUBLIC_OLLAMA_SYSTEM_PROMPT) ||
  [
    'You are {{tutor_name}}, a friendly Korean language teacher for beginners.',
    'Keep replies short (2–4 sentences). If the question is vague, ask one clarifying question first.',
    'Once the topic is clear, give a brief explanation and at most one example (Korean + English).',
    'Be warm and patient with light empathy; a gentle emoji is fine when it fits—keep encouragement brief.',
    'Prefer Soju vocabulary when helpful. Mix Korean and English naturally.',
    'Use plain text; **bold** for key Korean forms is fine. Write → for conjugation; avoid LaTeX and ---.',
  ].join(' ');

/** Overridable at runtime via ``GET /v1/soju/client-config`` (see ``applyClientConfig``). */
export let aiModel = firstDefined(dynamicPublicEnv.PUBLIC_AI_MODEL, dynamicPublicEnv.PUBLIC_OLLAMA_MODEL) ?? 'gemma4:e4b';
export let aiEmbedModel = firstDefined(dynamicPublicEnv.PUBLIC_AI_EMBED_MODEL, dynamicPublicEnv.PUBLIC_OLLAMA_EMBED_MODEL) ?? 'nomic-embed-text';
export let aiApiMode: AiApiMode = firstDefined(dynamicPublicEnv.PUBLIC_AI_API_MODE) === 'conversations' ? 'conversations' : 'chat-completions';
export let aiTutorName = firstDefined(dynamicPublicEnv.PUBLIC_AI_TUTOR_NAME) ?? defaultChatTutorName;
export let defaultChatSystemPrompt = envSystemPrompt;
export let chatSummaryTrigger = envChatThresholds.trigger;
export let chatKeepRecent = envChatThresholds.keepRecent;
export let localTtsVoice = firstDefined(dynamicPublicEnv.PUBLIC_TTS_PIPER_VOICE) ?? 'ko-KR-SunHiNeural';

/** Default TTS engine from env (user can override in Settings). */
export const defaultTtsEngine = resolveTtsEngine(dynamicPublicEnv.PUBLIC_TTS_ENGINE);

export type SojuClientConfigPayload = {
  ai_enabled?: boolean;
  api_mode?: string;
  chat_model?: string;
  embed_model?: string;
  tutor_name?: string;
  system_prompt?: string;
  chat_summary_trigger?: number;
  chat_keep_recent?: number;
  tts_default_voice?: string;
};

/** Apply non-secret bootstrap values from the Soju backend. */
export function applyClientConfig(payload: SojuClientConfigPayload): void {
  if (typeof payload.chat_model === 'string' && payload.chat_model.trim()) {
    aiModel = payload.chat_model.trim();
  }
  if (typeof payload.embed_model === 'string' && payload.embed_model.trim()) {
    aiEmbedModel = payload.embed_model.trim();
  }
  if (payload.api_mode === 'conversations' || payload.api_mode === 'chat-completions') {
    aiApiMode = payload.api_mode;
  }
  if (typeof payload.tutor_name === 'string' && payload.tutor_name.trim()) {
    aiTutorName = payload.tutor_name.trim();
  }
  if (typeof payload.system_prompt === 'string' && payload.system_prompt.trim()) {
    defaultChatSystemPrompt = payload.system_prompt;
  }
  if (typeof payload.tts_default_voice === 'string' && payload.tts_default_voice.trim()) {
    localTtsVoice = payload.tts_default_voice.trim();
  }
  if (payload.chat_summary_trigger !== undefined || payload.chat_keep_recent !== undefined) {
    const nextThresholds = resolveChatContextThresholds(
      payload.chat_summary_trigger !== undefined ? String(payload.chat_summary_trigger) : undefined,
      payload.chat_keep_recent !== undefined ? String(payload.chat_keep_recent) : undefined,
    );
    chatSummaryTrigger = nextThresholds.trigger;
    chatKeepRecent = nextThresholds.keepRecent;
  }
}
