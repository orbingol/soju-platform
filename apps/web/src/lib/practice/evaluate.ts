import { complete } from '$lib/ai/client';

export interface PracticeStoryEvaluateOptions {
  level: {
    label: string;
    guidance: string;
    grammarSummary?: string;
  };
  topic: string;
  userStory: string;
  /** Model story text (title + joined hangul sentences). */
  modelStory: string;
}

export interface PracticeStoryEvaluateResult {
  feedback: string;
}

const EVALUATE_TIMEOUT_MS = 60_000;
const EVALUATE_MAX_TOKENS = 800;

export function buildStoryEvaluatePrompt(options: PracticeStoryEvaluateOptions): string {
  const { level, topic, userStory, modelStory } = options;

  return `You are a Korean language tutor giving brief feedback on a beginner's written story.

Learner level: ${level.label}
${level.guidance}${level.grammarSummary ? `\n\n${level.grammarSummary}` : ''}

Story prompt (personal question the learner answered):
${topic}

Model reference story (for comparison only; do not demand the learner match it word-for-word):
${modelStory}

Learner's story:
${userStory}

Respond with valid JSON only (no markdown prose) using this shape:
{"feedback": "..."}

Requirements:
- "feedback" must be short English feedback only (2–4 sentences).
- Judge whether the learner answered the prompt as a short first-person narrative (not a dialogue).
- Mention grammar or vocabulary gently when useful.
- Do not rewrite the whole story; at most quote a tiny suggested fix.
- Do not include Korean romanization.`;
}

function parseFeedbackJson(text: string): PracticeStoryEvaluateResult {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error('The model returned empty feedback. Retry evaluate.');
  }

  let parsed: unknown;
  try {
    const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
    const jsonText = fenced ? fenced[1].trim() : trimmed;
    parsed = JSON.parse(jsonText);
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    throw new Error(`Invalid evaluate JSON: ${detail}`);
  }

  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error('Invalid evaluate JSON: root must be an object');
  }

  const feedback = (parsed as { feedback?: unknown }).feedback;
  if (typeof feedback !== 'string' || !feedback.trim()) {
    throw new Error('Invalid evaluate JSON: feedback must be a non-empty string');
  }

  return { feedback: feedback.trim() };
}

export async function evaluatePracticeStory(options: PracticeStoryEvaluateOptions): Promise<PracticeStoryEvaluateResult> {
  const content = await complete({
    messages: [
      { role: 'system', content: buildStoryEvaluatePrompt(options) },
      { role: 'user', content: 'Evaluate the learner story and return JSON feedback.' },
    ],
    jsonMode: true,
    temperature: 0.4,
    timeoutMs: EVALUATE_TIMEOUT_MS,
    maxTokens: EVALUATE_MAX_TOKENS,
    reasoningEffort: 'none',
  });

  return parseFeedbackJson(content);
}
