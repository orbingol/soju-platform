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
}

export interface AiClient {
  checkAvailable(): Promise<boolean>;
  complete(request: AiCompletionRequest): Promise<string>;
  stream(request: AiCompletionRequest): AsyncGenerator<string, void, unknown>;
}
