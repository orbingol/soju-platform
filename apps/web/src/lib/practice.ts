import { complete } from '$lib/ai/client';
import type { RetrievedGrammar } from '$lib/practice/retrieve';
import { parsePracticeJson, type PracticeSessionJson } from '$lib/staging';

export type PracticeExerciseType = 'sentences' | 'questions' | 'fill_in_blank' | 'story' | 'vocabulary_candidates';

/** Subset of `LevelConfig` needed for prompting (label/guidance/grammar summary). */
export interface PracticeLevelInfo {
  label: string;
  guidance: string;
  grammarSummary?: string;
}

export interface PracticeGenerateOptions {
  level: PracticeLevelInfo;
  /** Theme description (a preset theme's description, or free-form custom text). */
  themeText: string;
  exerciseType: PracticeExerciseType;
  /** Items in the primary section (story: sentence cap instead of exact count). */
  count: number;
  /** Retrieved hangul vocabulary for the theme/level (from `/api/practice/retrieve`). */
  hangul: string[];
  /** Retrieved grammar patterns for the level (from `/api/practice/retrieve`). */
  grammar: RetrievedGrammar[];
  /** Required by the UI when exerciseType is story; included in the system prompt. */
  storyTopic?: string;
}

interface ResponseSpec {
  shape: string;
  requirements: string[];
}

/** Local generation can be slow; give it more room than the shared chat timeout. */
const PRACTICE_TIMEOUT_MS = 120_000;

/** Rough output budget so a larger `count` doesn't get cut off, without an unbounded generation. */
const PRACTICE_BASE_MAX_TOKENS = 600;
const PRACTICE_TOKENS_PER_ITEM = 180;
const PRACTICE_MAX_TOKENS_CAP = 4000;

function estimateMaxTokens(count: number): number {
  return Math.min(PRACTICE_MAX_TOKENS_CAP, PRACTICE_BASE_MAX_TOKENS + count * PRACTICE_TOKENS_PER_ITEM);
}

const CANDIDATES_OPTIONAL_REQUIREMENT =
  '"vocabulary_candidates" is optional: at most 3 new words related to the theme (hangul + english only; no romanization); omit the field entirely if none fit.';

function buildResponseSpec(exerciseType: PracticeExerciseType, count: number): ResponseSpec {
  switch (exerciseType) {
    case 'sentences':
      return {
        shape: '{\n  "sentences": [{"hangul": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [
          `Exactly ${count} beginner sentence(s) in "sentences".`,
          'Each hangul value must be exactly one simple sentence (no multi-sentence stories, no clause chains).',
          CANDIDATES_OPTIONAL_REQUIREMENT,
        ],
      };
    case 'questions':
      return {
        shape: '{\n  "questions": [{"prompt": "...", "answer": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [
          `Exactly ${count} beginner question(s) in "questions".`,
          'Each item needs "prompt" (a direct question in Korean hangul only), "answer" (what the learner should produce in Korean), and "english" (English gloss of the prompt for a Translate button).',
          'Do NOT put English inside "prompt" (no parentheses glosses). Do NOT use speaker labels like "A:" or "B:", and do not write A–B dialogues.',
          CANDIDATES_OPTIONAL_REQUIREMENT,
        ],
      };
    case 'fill_in_blank':
      return {
        shape:
          '{\n  "fill_in_blank": [{"prompt": "카페에서 ___ 주세요", "answer": "커피", "english": "Please give me coffee at the café"}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [
          `Exactly ${count} fill-in-the-blank item(s) in "fill_in_blank".`,
          'Every "prompt" MUST contain the exact blank marker ___ (three underscores) exactly once — this is mandatory.',
          'Write 1–2 natural Korean sentences in hangul only; leave the missing word/phrase as ___; put the missing text in "answer"; put an English gloss of the full prompt in "english".',
          'Do NOT fill the blank with the answer in "prompt". Do NOT put English inside "prompt". Do NOT use speaker labels like "A:" or "B:".',
          CANDIDATES_OPTIONAL_REQUIREMENT,
        ],
      };
    case 'story':
      return {
        shape: '{\n  "story": {"title": "...", "sentences": [{"hangul": "...", "english": "..."}]},\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [
          `One short first-person story in "story" with about ${count} sentence(s) (aim for a paragraph of roughly 4–7 linked sentences; stay near ${count}).`,
          'The story prompt is a personal question the learner will answer (e.g. "What did you do last weekend?"). Write a model answer as a continuous narrative paragraph, not a list of unrelated lines.',
          'Do NOT write a dialogue, A–B conversation, interview, or Q&A. No speaker labels. No questions inside the story unless natural speech within one sentence.',
          'Each "sentences" item MUST be an object {"hangul":"...","english":"..."} — never a bare string.',
          'Stay at the learner level: simple connected ideas (who/where/what/why), like a short personal reply.',
          CANDIDATES_OPTIONAL_REQUIREMENT,
        ],
      };
    case 'vocabulary_candidates':
      return {
        shape: '{\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [`Exactly ${count} vocabulary item(s) in "vocabulary_candidates" (hangul and english required; do not include romanization).`],
      };
  }
}

function formatHangulList(hangul: string[]): string {
  return hangul.length > 0 ? hangul.join(', ') : '(none retrieved — use general beginner vocabulary instead)';
}

function formatGrammarList(grammar: RetrievedGrammar[]): string {
  if (grammar.length === 0) return '(none retrieved)';
  return grammar.map((pattern) => `- ${pattern.form} (${pattern.english})${pattern.summary ? `: ${pattern.summary}` : ''}`).join('\n');
}

export function buildPracticeSystemPrompt(options: PracticeGenerateOptions): string {
  const { level, themeText, exerciseType, hangul, grammar, storyTopic } = options;
  const count = Math.max(1, Math.floor(options.count));
  const spec = buildResponseSpec(exerciseType, count);

  const storyTopicLine = exerciseType === 'story' && storyTopic?.trim() ? `\n\nStory prompt (personal question to answer in first person):\n${storyTopic.trim()}` : '';

  return `You are a Korean language tutor creating a beginner practice session.

Learner level: ${level.label}
${level.guidance}${level.grammarSummary ? `\n\n${level.grammarSummary}` : ''}

Theme: ${themeText}${storyTopicLine}

Prefer this vocabulary when it fits the theme (hangul only; do not invent unrelated words):
${formatHangulList(hangul)}

Prefer these grammar patterns for this level when they fit:
${formatGrammarList(grammar)}

Respond with valid JSON only (no markdown prose) using this shape:
${spec.shape}

Requirements:
${spec.requirements.map((requirement) => `- ${requirement}`).join('\n')}
- Keep hangul natural and beginner-friendly.
- Do not include romanization fields anywhere in the JSON.`;
}

export async function generatePracticeSession(options: PracticeGenerateOptions): Promise<PracticeSessionJson> {
  const count = Math.max(1, Math.floor(options.count));
  const content = await complete({
    messages: [
      { role: 'system', content: buildPracticeSystemPrompt(options) },
      { role: 'user', content: "Generate today's practice session JSON." },
    ],
    jsonMode: true,
    temperature: 0.6,
    timeoutMs: PRACTICE_TIMEOUT_MS,
    maxTokens: estimateMaxTokens(count),
    // Reasoning models (gemma4, etc.) otherwise fill max_tokens with a reasoning
    // trace and return empty content → "unexpected end of data" in JSON.parse.
    reasoningEffort: 'none',
  });

  if (!content.trim()) {
    throw new Error(
      'The model returned an empty response. If you use a thinking model (e.g. gemma4), retry — Practice disables thinking for JSON generation. Otherwise try a smaller count.',
    );
  }

  return parsePracticeJson(content);
}

export { buildStoryEvaluatePrompt, evaluatePracticeStory, type PracticeStoryEvaluateOptions, type PracticeStoryEvaluateResult } from '$lib/practice/evaluate';
