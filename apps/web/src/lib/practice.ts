import { complete } from '$lib/ai/client';
import { parsePracticeJson, type PracticeSessionJson } from '$lib/staging';

export function buildPracticeSystemPrompt(vocabulary: {
  words: Array<{ hangul: string; romanization: string; english: string }>;
  verbs: Array<{ hangul: string; romanization: string; english: string }>;
}): string {
  const wordLines = vocabulary.words.map((w) => `- ${w.hangul} (${w.romanization}): ${w.english}`).join('\n');
  const verbLines = vocabulary.verbs.map((v) => `- ${v.hangul} (${v.romanization}): ${v.english}`).join('\n');

  return `You are a Korean language tutor creating a beginner practice session.

Use primarily this vocabulary:
Words:
${wordLines}

Verbs:
${verbLines}

You may introduce up to 3 related new words as vocabulary_candidates.

Respond with valid JSON only (no markdown prose) using this shape:
{
  "sentences": [{"hangul": "...", "romanization": "...", "english": "..."}],
  "questions": [{"question": "...", "answer": "...", "hangul": "...", "english": "..."}],
  "fill_in_blank": [{"sentence": "...", "blank": "...", "answer": "...", "english": "..."}],
  "story": {"title": "...", "sentences": [{"hangul": "...", "english": "..."}]},
  "vocabulary_candidates": [{"hangul": "...", "romanization": "...", "english": "..."}]
}

Requirements:
- Exactly 5 beginner sentences
- Exactly 5 questions
- Exactly 5 fill-in-the-blank items
- One tiny story with 4-5 sentences
- Keep hangul natural and beginner-friendly`;
}

export async function generatePracticeSession(vocabulary: {
  words: Array<{ hangul: string; romanization: string; english: string }>;
  verbs: Array<{ hangul: string; romanization: string; english: string }>;
}): Promise<PracticeSessionJson> {
  const content = await complete({
    messages: [
      { role: 'system', content: buildPracticeSystemPrompt(vocabulary) },
      { role: 'user', content: "Generate today's practice session JSON." },
    ],
    jsonMode: true,
    temperature: 0.6,
  });

  return parsePracticeJson(content);
}
