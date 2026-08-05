import { jsonPost, readError } from '$lib/ai/http';
import type { PracticeSessionJson } from '$lib/staging';

export type PracticeExerciseType = 'sentences' | 'questions' | 'fill_in_blank' | 'story' | 'vocabulary_candidates';

export interface PracticeGenerateOptions {
  /** Course level id (e.g. ``1A``). */
  levelId: string;
  /** Theme description (a preset theme's description, or free-form custom text). */
  themeText: string;
  exerciseType: PracticeExerciseType;
  /** Items in the primary section (story: sentence cap instead of exact count). */
  count: number;
  /** Include unassigned-level vocab/grammar in backend retrieval. */
  includeUnassigned?: boolean;
  /** Required by the UI when exerciseType is story. */
  storyTopic?: string;
  /** Prior sample to avoid repeating when regenerating a story. */
  previousStory?: { title?: string; sentences: Array<{ hangul: string; english: string }> };
}

export interface PracticeStoryEvaluateOptions {
  levelId: string;
  topic: string;
  userStory: string;
  /** Model story text (title + joined hangul sentences). */
  modelStory: string;
}

export interface PracticeStoryEvaluateResult {
  feedback: string;
}

/** Local generation can be slow; give it more room than the shared chat timeout. */
const PRACTICE_TIMEOUT_MS = 120_000;
const EVALUATE_TIMEOUT_MS = 60_000;

async function readPracticeError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown; error?: string };
    if (typeof body.error === 'string' && body.error.trim()) return body.error;
    if (typeof body.detail === 'string' && body.detail.trim()) return body.detail;
    if (Array.isArray(body.detail)) {
      const parts = body.detail
        .map((item) => (typeof item === 'object' && item && 'msg' in item ? String((item as { msg: unknown }).msg) : String(item)))
        .filter(Boolean);
      if (parts.length) return parts.join('; ');
    }
  } catch {
    // fall through to generic error text
  }
  return readError(response);
}

/** Generate a practice session via the Soju backend (embed + retrieve + LLM server-side). */
export async function generatePracticeSession(options: PracticeGenerateOptions): Promise<PracticeSessionJson> {
  const count = Math.max(1, Math.floor(options.count));
  const response = await jsonPost(
    '/v1/soju/practice/generate',
    {
      level: options.levelId,
      theme_text: options.themeText,
      exercise_type: options.exerciseType,
      count,
      include_unassigned: options.includeUnassigned === true,
      ...(options.storyTopic?.trim() ? { story_topic: options.storyTopic.trim() } : {}),
      ...(options.previousStory ? { previous_story: options.previousStory } : {}),
    },
    PRACTICE_TIMEOUT_MS,
  );
  if (!response.ok) {
    throw new Error(await readPracticeError(response));
  }
  return (await response.json()) as PracticeSessionJson;
}

/** Evaluate a learner story via the Soju backend. */
export async function evaluatePracticeStory(options: PracticeStoryEvaluateOptions): Promise<PracticeStoryEvaluateResult> {
  const response = await jsonPost(
    '/v1/soju/practice/evaluate-story',
    {
      level: options.levelId,
      topic: options.topic,
      user_story: options.userStory,
      model_story: options.modelStory,
    },
    EVALUATE_TIMEOUT_MS,
  );
  if (!response.ok) {
    throw new Error(await readPracticeError(response));
  }
  return (await response.json()) as PracticeStoryEvaluateResult;
}
