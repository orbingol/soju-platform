export interface PracticeSentence {
  hangul: string;
  english: string;
}

export interface PracticeQuestion {
  prompt: string;
  answer: string;
  english?: string;
}

export interface PracticeFillBlank {
  prompt: string;
  answer: string;
  english?: string;
}

export interface PracticeStory {
  title?: string;
  sentences: PracticeSentence[];
  sequel_of?: string;
}

export interface PracticeVocabularyCandidate {
  hangul: string;
  english: string;
  examples?: Array<{ hangul: string; english: string }>;
}

export interface PracticeSessionJson {
  sentences?: PracticeSentence[];
  questions?: PracticeQuestion[];
  fill_in_blank?: PracticeFillBlank[];
  story?: PracticeStory;
  vocabulary_candidates?: PracticeVocabularyCandidate[];
}

export interface StagingExercisesDoc {
  staging: true;
  date: string;
  exercises: {
    sentences: PracticeSentence[];
    questions: PracticeQuestion[];
    fill_in_blank: PracticeFillBlank[];
  };
}

export interface StagingStoriesDoc {
  staging: true;
  date: string;
  story: PracticeStory;
}

export interface StagingVocabularyDoc {
  staging: true;
  entries: Array<{
    id: string;
    hangul: string;
    english: string;
    examples?: Array<{ id: string; hangul: string; english: string }>;
  }>;
}

export function todayIsoDate(date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function requireString(value: unknown, path: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`Invalid practice JSON: ${path} must be a non-empty string`);
  }
  return value;
}

function optionalString(value: unknown, path: string): string | undefined {
  if (value === undefined || value === null) return undefined;
  if (typeof value !== 'string') {
    throw new Error(`Invalid practice JSON: ${path} must be a string`);
  }
  return value;
}

function parseSentence(value: unknown, path: string): PracticeSentence {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  return {
    hangul: requireString(value.hangul, `${path}.hangul`),
    english: requireString(value.english, `${path}.english`),
  };
}

/** Story models often emit bare hangul strings; coerce those and allow missing english. */
function parseStorySentence(value: unknown, path: string): PracticeSentence {
  if (typeof value === 'string') {
    const hangul = value.trim();
    if (!hangul) {
      throw new Error(`Invalid practice JSON: ${path} must be a non-empty string or object`);
    }
    return { hangul, english: '' };
  }
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  const hangul =
    optionalString(value.hangul, `${path}.hangul`) ??
    optionalString(value.korean, `${path}.korean`) ??
    optionalString(value.text, `${path}.text`);
  if (!hangul?.trim()) {
    throw new Error(`Invalid practice JSON: ${path}.hangul must be a non-empty string`);
  }
  const english =
    optionalString(value.english, `${path}.english`) ??
    optionalString(value.en, `${path}.en`) ??
    '';
  return { hangul: hangul.trim(), english: english.trim() };
}

function parseQuestion(value: unknown, path: string): PracticeQuestion {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  return {
    prompt: requireString(value.prompt, `${path}.prompt`),
    answer: requireString(value.answer, `${path}.answer`),
    english: optionalString(value.english, `${path}.english`),
  };
}

/**
 * Models often omit `___`, use long underscores, or leave the answer filled in.
 * Normalize so every fill-in-blank prompt has a visible blank.
 */
export function normalizeFillBlankPrompt(prompt: string, answer: string): string {
  let text = prompt.trim();

  text = text
    .replace(/_{2,}/g, '___')
    .replace(/[□■◻▪]+/g, '___')
    .replace(/[○●◯ㅇ]{2,}/g, '___')
    .replace(/（\s*）/g, '___')
    .replace(/\(\s*\)/g, '___')
    .replace(/［\s*］/g, '___')
    .replace(/\[\s*\]/g, '___')
    .replace(/…+/g, '___')
    .replace(/(?:___\s*){2,}/g, '___ ');

  if (text.includes('___')) {
    return text.trim();
  }

  const ans = answer.trim();
  if (ans && text.includes(ans)) {
    return text.replace(ans, '___').trim();
  }

  // Last resort: blank the first Hangul (or Latin) word so a gap always appears.
  return text.replace(/[가-힣A-Za-z0-9]+/u, '___').trim();
}

function parseFillBlank(value: unknown, path: string): PracticeFillBlank {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  const answer = requireString(value.answer, `${path}.answer`);
  const prompt = normalizeFillBlankPrompt(requireString(value.prompt, `${path}.prompt`), answer);
  return {
    prompt,
    answer,
    english: optionalString(value.english, `${path}.english`),
  };
}

/** Split a model paragraph into sentence-like chunks when it returns one string. */
function splitStoryParagraph(text: string): string[] {
  const parts = text
    .split(/(?<=[.!?。！？])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  return parts.length > 0 ? parts : [text.trim()];
}

function parseStory(value: unknown, path: string): PracticeStory {
  // Some models return the whole story as a single hangul paragraph string.
  if (typeof value === 'string') {
    const hangul = value.trim();
    if (!hangul) {
      throw new Error(`Invalid practice JSON: ${path} must be a non-empty string or object`);
    }
    return {
      sentences: splitStoryParagraph(hangul).map((sentence) => ({ hangul: sentence, english: '' })),
    };
  }

  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }

  let rawSentences = value.sentences;

  // Alternate keys some models use.
  if (rawSentences === undefined) {
    rawSentences = value.paragraph ?? value.text ?? value.body;
  }

  if (typeof rawSentences === 'string') {
    const hangul = rawSentences.trim();
    if (!hangul) {
      throw new Error(`Invalid practice JSON: ${path}.sentences must be a non-empty string or array`);
    }
    return {
      title: optionalString(value.title, `${path}.title`),
      sentences: splitStoryParagraph(hangul).map((sentence) => ({ hangul: sentence, english: '' })),
      sequel_of: optionalString(value.sequel_of, `${path}.sequel_of`),
    };
  }

  if (!Array.isArray(rawSentences)) {
    throw new Error(`Invalid practice JSON: ${path}.sentences must be an array`);
  }
  if (rawSentences.length === 0) {
    throw new Error(`Invalid practice JSON: ${path}.sentences must not be empty`);
  }

  return {
    title: optionalString(value.title, `${path}.title`),
    sentences: rawSentences.map((item, index) => parseStorySentence(item, `${path}.sentences[${index}]`)),
    sequel_of: optionalString(value.sequel_of, `${path}.sequel_of`),
  };
}

function parseVocabularyCandidate(value: unknown, path: string): PracticeVocabularyCandidate {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  const examples = value.examples;
  return {
    hangul: requireString(value.hangul, `${path}.hangul`),
    english: requireString(value.english, `${path}.english`),
    examples: Array.isArray(examples)
      ? examples.map((item, index) => {
          if (!isRecord(item)) {
            throw new Error(`Invalid practice JSON: ${path}.examples[${index}] must be an object`);
          }
          return {
            hangul: requireString(item.hangul, `${path}.examples[${index}].hangul`),
            english: requireString(item.english, `${path}.examples[${index}].english`),
          };
        })
      : undefined,
  };
}

/** Validate unknown JSON into a typed practice session (rejects malformed AI output). */
export function validatePracticeSessionJson(raw: unknown): PracticeSessionJson {
  if (!isRecord(raw)) {
    throw new Error('Invalid practice JSON: root must be an object');
  }

  const session: PracticeSessionJson = {};

  if (raw.sentences !== undefined) {
    if (!Array.isArray(raw.sentences)) {
      throw new Error('Invalid practice JSON: sentences must be an array');
    }
    session.sentences = raw.sentences.map((item, index) => parseSentence(item, `sentences[${index}]`));
  }

  if (raw.questions !== undefined) {
    if (!Array.isArray(raw.questions)) {
      throw new Error('Invalid practice JSON: questions must be an array');
    }
    session.questions = raw.questions.map((item, index) => parseQuestion(item, `questions[${index}]`));
  }

  if (raw.fill_in_blank !== undefined) {
    if (!Array.isArray(raw.fill_in_blank)) {
      throw new Error('Invalid practice JSON: fill_in_blank must be an array');
    }
    session.fill_in_blank = raw.fill_in_blank.map((item, index) => parseFillBlank(item, `fill_in_blank[${index}]`));
  }

  if (raw.story !== undefined) {
    session.story = parseStory(raw.story, 'story');
  }

  if (raw.vocabulary_candidates !== undefined) {
    if (!Array.isArray(raw.vocabulary_candidates)) {
      throw new Error('Invalid practice JSON: vocabulary_candidates must be an array');
    }
    session.vocabulary_candidates = raw.vocabulary_candidates.map((item, index) => parseVocabularyCandidate(item, `vocabulary_candidates[${index}]`));
  }

  return session;
}

export function normalizePracticeSession(
  raw: PracticeSessionJson,
  date = todayIsoDate(),
): {
  exercises: StagingExercisesDoc;
  stories: StagingStoriesDoc | null;
  vocabulary: StagingVocabularyDoc | null;
} {
  const exercises: StagingExercisesDoc = {
    staging: true,
    date,
    exercises: {
      sentences: raw.sentences ?? [],
      questions: raw.questions ?? [],
      fill_in_blank: raw.fill_in_blank ?? [],
    },
  };

  const story = raw.story;
  const stories =
    story && story.sentences.length > 0
      ? {
          staging: true as const,
          date,
          story: {
            title: story.title,
            sentences: story.sentences,
            sequel_of: story.sequel_of,
          },
        }
      : null;

  const candidates = raw.vocabulary_candidates ?? [];
  const vocabulary =
    candidates.length > 0
      ? {
          staging: true as const,
          entries: candidates.map((entry) => ({
            id: crypto.randomUUID(),
            hangul: entry.hangul,
            english: entry.english,
            examples: entry.examples?.map((example) => ({
              id: crypto.randomUUID(),
              hangul: example.hangul,
              english: example.english,
            })),
          })),
        }
      : null;

  return { exercises, stories, vocabulary };
}

/** Rough heuristic: does `text` look like it was cut off mid-object/array (unclosed brace/bracket)? */
function looksTruncated(text: string): boolean {
  const trimmed = text.trimEnd();
  if (!trimmed) return false;
  if (!trimmed.endsWith('}') && !trimmed.endsWith(']')) return true;
  const opens = (trimmed.match(/[{[]/g) ?? []).length;
  const closes = (trimmed.match(/[}\]]/g) ?? []).length;
  return opens !== closes;
}

/** Strip optional markdown fences; tolerate an unclosed opening ```json fence. */
function extractJsonText(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return '';

  const closed = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (closed) return closed[1].trim();

  const openFence = trimmed.match(/^```(?:json)?\s*([\s\S]*)$/i);
  if (openFence) return openFence[1].trim();

  return trimmed;
}

export function parsePracticeJson(text: string): PracticeSessionJson {
  const jsonText = extractJsonText(text);
  if (!jsonText) {
    throw new Error('Invalid practice JSON: the model returned an empty body. Retry, or try a smaller count — thinking models can exhaust the output budget before emitting JSON.');
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch (err) {
    if (looksTruncated(jsonText)) {
      throw new Error('The model response looks truncated (JSON did not finish). Try a smaller count, or retry — generation may have hit a length or time limit.');
    }
    const detail = err instanceof Error ? err.message : String(err);
    throw new Error(`Invalid practice JSON: ${detail}`);
  }
  return validatePracticeSessionJson(parsed);
}

export function downloadTextFile(filename: string, content: string, mime = 'text/yaml'): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
