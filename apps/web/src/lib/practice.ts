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
}

interface ResponseSpec {
  shape: string;
  requirements: string[];
}

/** Local generation can be slow; give it more room than the shared chat timeout. */
const PRACTICE_TIMEOUT_MS = 120_000;

/** Rough output budget so a larger `count` doesn't get cut off, without an unbounded generation. */
const PRACTICE_BASE_MAX_TOKENS = 300;
const PRACTICE_TOKENS_PER_ITEM = 150;
const PRACTICE_MAX_TOKENS_CAP = 2000;

function estimateMaxTokens(count: number): number {
  return Math.min(PRACTICE_MAX_TOKENS_CAP, PRACTICE_BASE_MAX_TOKENS + count * PRACTICE_TOKENS_PER_ITEM);
}

const CANDIDATES_OPTIONAL_REQUIREMENT =
  '"vocabulary_candidates" is optional: at most 3 new words related to the theme (hangul + english required); omit the field entirely if none fit.';

function buildResponseSpec(exerciseType: PracticeExerciseType, count: number): ResponseSpec {
  switch (exerciseType) {
    case 'sentences':
      return {
        shape: '{\n  "sentences": [{"hangul": "...", "romanization": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [`Exactly ${count} beginner sentence(s) in "sentences".`, CANDIDATES_OPTIONAL_REQUIREMENT],
      };
    case 'questions':
      return {
        shape: '{\n  "questions": [{"question": "...", "answer": "...", "hangul": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [`Exactly ${count} beginner question(s) in "questions".`, CANDIDATES_OPTIONAL_REQUIREMENT],
      };
    case 'fill_in_blank':
      return {
        shape:
          '{\n  "fill_in_blank": [{"sentence": "...", "blank": "...", "answer": "...", "english": "..."}],\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [`Exactly ${count} fill-in-the-blank item(s) in "fill_in_blank".`, CANDIDATES_OPTIONAL_REQUIREMENT],
      };
    case 'story':
      return {
        shape: '{\n  "story": {"title": "...", "sentences": [{"hangul": "...", "english": "..."}]},\n  "vocabulary_candidates": [{"hangul": "...", "english": "..."}]\n}',
        requirements: [`One short story in "story" with at most ${count} sentence(s).`, CANDIDATES_OPTIONAL_REQUIREMENT],
      };
    case 'vocabulary_candidates':
      return {
        shape: '{\n  "vocabulary_candidates": [{"hangul": "...", "romanization": "...", "english": "..."}]\n}',
        requirements: [`Exactly ${count} vocabulary candidate(s) in "vocabulary_candidates" (hangul, romanization, and english all required).`],
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
  const { level, themeText, exerciseType, hangul, grammar } = options;
  const count = Math.max(1, Math.floor(options.count));
  const spec = buildResponseSpec(exerciseType, count);

  return `You are a Korean language tutor creating a beginner practice session.

Learner level: ${level.label}
${level.guidance}${level.grammarSummary ? `\n\n${level.grammarSummary}` : ''}

Theme: ${themeText}

Prefer this vocabulary when it fits the theme (hangul only; do not invent unrelated words):
${formatHangulList(hangul)}

Prefer these grammar patterns for this level when they fit:
${formatGrammarList(grammar)}

Respond with valid JSON only (no markdown prose) using this shape:
${spec.shape}

Requirements:
${spec.requirements.map((requirement) => `- ${requirement}`).join('\n')}
- Keep hangul natural and beginner-friendly.`;
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
  });

  return parsePracticeJson(content);
}
