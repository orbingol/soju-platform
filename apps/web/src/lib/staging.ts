export interface PracticeSentence {
  hangul: string;
  english: string;
  romanization?: string;
}

export interface PracticeQuestion {
  question: string;
  answer: string;
  hangul?: string;
  english?: string;
}

export interface PracticeFillBlank {
  sentence: string;
  blank: string;
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
  romanization: string;
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
    romanization: string;
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
    romanization: optionalString(value.romanization, `${path}.romanization`),
  };
}

function parseQuestion(value: unknown, path: string): PracticeQuestion {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  return {
    question: requireString(value.question, `${path}.question`),
    answer: requireString(value.answer, `${path}.answer`),
    hangul: optionalString(value.hangul, `${path}.hangul`),
    english: optionalString(value.english, `${path}.english`),
  };
}

function parseFillBlank(value: unknown, path: string): PracticeFillBlank {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  return {
    sentence: requireString(value.sentence, `${path}.sentence`),
    blank: requireString(value.blank, `${path}.blank`),
    answer: requireString(value.answer, `${path}.answer`),
    english: optionalString(value.english, `${path}.english`),
  };
}

function parseStory(value: unknown, path: string): PracticeStory {
  if (!isRecord(value)) {
    throw new Error(`Invalid practice JSON: ${path} must be an object`);
  }
  if (!Array.isArray(value.sentences)) {
    throw new Error(`Invalid practice JSON: ${path}.sentences must be an array`);
  }
  return {
    title: optionalString(value.title, `${path}.title`),
    sentences: value.sentences.map((item, index) => parseSentence(item, `${path}.sentences[${index}]`)),
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
    romanization: requireString(value.romanization, `${path}.romanization`),
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
            romanization: entry.romanization,
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

export function parsePracticeJson(text: string): PracticeSessionJson {
  const trimmed = text.trim();
  const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
  const jsonText = fenced ? fenced[1].trim() : trimmed;
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch (err) {
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
