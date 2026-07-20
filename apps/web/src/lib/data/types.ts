export interface Example {
  hangul: string;
  english: string;
}

export interface VocabularyEntry {
  id: string;
  hangul: string;
  romanization: string;
  english: string;
  type: string;
  level?: string;
  visibility?: 'visible' | 'hidden';
  grammar_pattern?: string;
}

export interface VerbEntry extends VocabularyEntry {
  type: 'verb';
  forms: Record<string, Record<string, string>>;
  examples?: Record<string, Record<string, Example[]>>;
}

export interface FieldColumn {
  label: string;
  subtitle?: string;
}

export interface ConjugationColumn {
  variant: string;
  label: string;
  subtitle: string;
  join?: string[];
  separator?: string;
}

export interface TableSection {
  id: string;
  label: string;
  description?: string;
  css: string;
  columns: ConjugationColumn[];
}

export interface VerbTableLayout {
  fields: {
    hangul: FieldColumn;
    romanization?: FieldColumn;
    english: FieldColumn;
  };
  sections: TableSection[];
}

export interface DefaultTableLayout {
  fields: {
    hangul: FieldColumn;
    romanization?: FieldColumn;
    english: FieldColumn;
  };
  examples?: { label: string };
}

export interface VocabularyType {
  id: string;
  slug: string;
  label: string;
}

export interface TopicMeta {
  id: string;
  label: string;
  description?: string;
}

export interface TopicSection {
  id: string;
  label: string;
  description?: string;
  entries: ResolvedEntry[];
}

export interface ResolvedEntry {
  id: string;
  hangul: string;
  romanization: string;
  english: string;
  type: string;
  visibility?: 'visible' | 'hidden';
  examples?: Example[];
}

export interface TopicEntryRef {
  ref: string;
}

export interface TopicEntryLocal {
  id: string;
  local: true;
  hangul: string;
  romanization: string;
  english: string;
  type?: string;
  examples?: Example[];
}

export type TopicEntry = TopicEntryRef | TopicEntryLocal;

export type GrammarCategory =
  | 'particles'
  | 'time_place'
  | 'verb_patterns'
  | 'question_words'
  | 'connectors';

export interface GrammarCategoryInfo {
  id: GrammarCategory;
  slug: string;
  label: string;
  description: string;
}

export interface GrammarPatternMeta {
  id: string;
  label: string;
  form: string;
  english: string;
  category: GrammarCategory;
  description?: string;
  path: string;
}

export interface GrammarExample {
  hangul: string;
  english: string;
}

export interface GrammarSection {
  id: string;
  label: string;
  description?: string;
  examples: GrammarExample[];
}

export interface GrammarConversationTurn {
  speaker: string;
  hangul: string;
  english: string;
}

export interface GrammarConversation {
  title: string;
  turns: GrammarConversationTurn[];
}

export interface GrammarPatternPage {
  id: string;
  form: string;
  romanization: string;
  english: string;
  category: GrammarCategory;
  summary: string;
  notes?: string[];
  sections: GrammarSection[];
  conversations?: GrammarConversation[];
  phrase_refs?: string[];
}

export interface PracticeTheme {
  id: string;
  label: string;
  description: string;
}

export interface LevelConfig {
  id: string;
  label: string;
  description: string;
  guidance: string;
  grammarSummary?: string;
  includeLevels?: string[];
}

export interface LevelsConfig {
  default: string;
  levels: LevelConfig[];
}
