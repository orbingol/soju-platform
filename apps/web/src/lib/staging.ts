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
  return JSON.parse(jsonText) as PracticeSessionJson;
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
