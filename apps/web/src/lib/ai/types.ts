export interface AiMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AiCompletionRequest {
  model?: string;
  messages: AiMessage[];
  stream?: boolean;
  jsonMode?: boolean;
  temperature?: number;
  /** Scopes server-side conversation storage (chat only). */
  sessionKey?: string;
  /** Optional abort for the underlying fetch. */
  signal?: AbortSignal;
  /** Per-request fetch timeout override (default: `AI_FETCH_TIMEOUT_MS`). */
  timeoutMs?: number;
  /** Caps generated output length (`max_tokens` / `max_output_tokens` depending on API mode). */
  maxTokens?: number;
  /**
   * Ollama OpenAI-compat thinking control (`reasoning_effort`).
   * Use `"none"` for JSON tasks so reasoning models (e.g. gemma4) don't spend the whole
   * `max_tokens` budget on a `reasoning` trace and return empty `content`.
   */
  reasoningEffort?: 'none' | 'low' | 'medium' | 'high';
}

export interface AiClient {
  checkAvailable(): Promise<boolean>;
  complete(request: AiCompletionRequest): Promise<string>;
  stream(request: AiCompletionRequest): AsyncGenerator<string, void, unknown>;
}
