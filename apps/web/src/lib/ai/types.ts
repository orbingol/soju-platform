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
}

export interface AiClient {
  checkAvailable(): Promise<boolean>;
  complete(request: AiCompletionRequest): Promise<string>;
  stream(request: AiCompletionRequest): AsyncGenerator<string, void, unknown>;
}
