<script lang="ts">
  import { untrack } from 'svelte';
  import yaml from 'yaml';

  import AiServiceGate from '$lib/components/AiServiceGate.svelte';
  import SpeakButton from '$lib/components/SpeakButton.svelte';
  import { evaluatePracticeStory, generatePracticeSession, type PracticeExerciseType } from '$lib/practice';
  import { fetchRetrieval, savePracticeSessionToStaging } from '$lib/practice/client';
  import { embedQueryText } from '$lib/practice/embed-query';
  import { downloadTextFile, normalizePracticeSession, todayIsoDate, type PracticeSessionJson } from '$lib/staging';

  let { data } = $props();

  const CUSTOM_THEME_ID = '__custom__';

  let selectedLevel = $state(untrack(() => data.defaultLevel));
  let selectedTheme = $state(untrack(() => data.themes[0]?.id ?? CUSTOM_THEME_ID));
  let customThemeText = $state('');
  let exerciseType = $state<PracticeExerciseType>('sentences');
  let count = $state(5);

  let loading = $state(false);
  let error = $state('');
  let status = $state('');
  let session = $state<PracticeSessionJson | null>(null);
  let resultType = $state<PracticeExerciseType | null>(null);

  let answers = $state<Record<number, string>>({});
  let revealed = $state<Record<number, boolean>>({});
  let promptTranslated = $state<Record<number, boolean>>({});

  let storyTopic = $state('');
  let userStory = $state('');
  let storyFeedback = $state('');
  let storyEvaluating = $state(false);
  let showModelTranslation = $state(false);

  const isCustomTheme = $derived(selectedTheme === CUSTOM_THEME_ID);
  const isStory = $derived(exerciseType === 'story');

  const STORY_TOPIC_SEEDS = [
    'What did you do last weekend?',
    'Where would you go on a holiday?',
    'What is a typical day like for you?',
    'Who is someone important in your family, and why?',
    'What did you eat yesterday, and where?',
    'What do you usually do after class or work?',
    'Tell me about a place you like in your city.',
    'What are you studying or learning right now, and why?',
    'Describe a time you helped a friend.',
    'What do you want to do this coming weekend?',
    'Where do you like to go shopping, and what do you buy?',
    'Tell me about your morning routine.',
  ] as const;

  function pickRandomStoryTopic() {
    const current = storyTopic.trim();
    const pool = STORY_TOPIC_SEEDS.filter((topic) => topic !== current);
    const choices = pool.length > 0 ? pool : [...STORY_TOPIC_SEEDS];
    storyTopic = choices[Math.floor(Math.random() * choices.length)] ?? 'What did you do last weekend?';
  }

  /** Models sometimes append "(English…)" on the prompt; peel that off for display/TTS. */
  function splitPromptEnglish(prompt: string, english?: string): { text: string; translation: string } {
    const match = prompt.match(/^(.*?)\s*\(([^)]*[A-Za-z][^)]*)\)\s*$/s);
    if (match?.[1] && match[2]) {
      return {
        text: match[1].trim(),
        translation: english?.trim() || match[2].trim(),
      };
    }
    return { text: prompt, translation: english?.trim() ?? '' };
  }

  function resetItemState() {
    answers = {};
    revealed = {};
    promptTranslated = {};
    storyFeedback = '';
    showModelTranslation = false;
  }

  function revealItem(index: number) {
    revealed = { ...revealed, [index]: true };
  }

  function togglePromptTranslation(index: number) {
    promptTranslated = { ...promptTranslated, [index]: !promptTranslated[index] };
  }

  function setAnswer(index: number, value: string) {
    answers = { ...answers, [index]: value };
  }

  function resolveThemeText(): string | null {
    if (isCustomTheme) {
      const themeText = customThemeText.trim();
      if (!themeText) {
        error = 'Enter a custom theme description first.';
        return null;
      }
      return themeText;
    }
    const theme = data.themes.find((entry) => entry.id === selectedTheme);
    if (!theme) {
      error = `Unknown theme ${selectedTheme}`;
      return null;
    }
    return theme.description;
  }

  async function generate() {
    error = '';
    status = '';

    const level = data.levels.find((entry) => entry.id === selectedLevel);
    if (!level) {
      error = `Unknown level ${selectedLevel}`;
      return;
    }

    const themeText = resolveThemeText();
    if (!themeText) return;

    if (exerciseType === 'story' && !storyTopic.trim()) {
      error = 'Enter a story prompt first.';
      return;
    }

    loading = true;
    try {
      status = 'Embedding theme…';
      const embedText = exerciseType === 'story' ? `${themeText}\n${storyTopic.trim()}` : themeText;
      const queryVector = await embedQueryText(embedText);

      status = 'Retrieving vocabulary and grammar…';
      const retrieved = await fetchRetrieval(selectedLevel, queryVector);

      status = exerciseType === 'story' ? 'Generating model story…' : 'Generating session…';
      session = await generatePracticeSession({
        level: { label: level.label, guidance: level.guidance, grammarSummary: level.grammarSummary },
        themeText,
        exerciseType,
        count,
        hangul: retrieved.hangul,
        grammar: retrieved.grammar,
        storyTopic: exerciseType === 'story' ? storyTopic.trim() : undefined,
      });
      resultType = exerciseType;
      resetItemState();
      status = exerciseType === 'story' ? 'Model story ready.' : 'Session ready.';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Generation failed';
      status = '';
    } finally {
      loading = false;
    }
  }

  async function evaluateStory() {
    if (!session?.story) return;
    error = '';
    storyFeedback = '';

    const level = data.levels.find((entry) => entry.id === selectedLevel);
    if (!level) {
      error = `Unknown level ${selectedLevel}`;
      return;
    }

    const draft = userStory.trim();
    if (!draft) {
      error = 'Write your story before evaluating.';
      return;
    }

    const topic = storyTopic.trim() || 'Untitled';
    const title = session.story.title?.trim();
    const hangulLines = session.story.sentences.map((sentence) => sentence.hangul).join('\n');
    const modelStory = title ? `${title}\n${hangulLines}` : hangulLines;

    storyEvaluating = true;
    try {
      status = 'Evaluating story…';
      const result = await evaluatePracticeStory({
        level: { label: level.label, guidance: level.guidance, grammarSummary: level.grammarSummary },
        topic,
        userStory: draft,
        modelStory,
      });
      storyFeedback = result.feedback;
      status = 'Feedback ready.';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Evaluate failed';
      status = '';
    } finally {
      storyEvaluating = false;
    }
  }

  function exportYaml() {
    if (!session) return;
    const docs = normalizePracticeSession(session);
    const date = todayIsoDate();

    downloadTextFile(`exercises-${date}.yaml`, yaml.stringify(docs.exercises));
    if (docs.stories) {
      downloadTextFile(`story-${date}.yaml`, yaml.stringify(docs.stories));
    }
    if (docs.vocabulary) {
      downloadTextFile('vocabulary-candidates.yaml', yaml.stringify(docs.vocabulary));
    }
    status = 'Downloaded staging YAML files.';
  }

  async function saveToStaging() {
    if (!session) return;
    const docs = normalizePracticeSession(session);
    const date = todayIsoDate();
    status = 'Saving to data/staging…';

    try {
      await savePracticeSessionToStaging(docs, date);
      status = 'Saved under data/staging/ (dev only).';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Save failed';
    }
  }
</script>

<svelte:head>
  <title>Practice · Education · Soju (소주)</title>
</svelte:head>

<h1>Practice</h1>
<p>Generate a beginner practice session for a level and theme, grounded in your canonical vocabulary and grammar.</p>

<AiServiceGate featureLabel="Practice">
  <div class="practice-app">
    <div class="practice-controls">
      <label class="practice-control">
        <span class="practice-control__label">Level</span>
        <select bind:value={selectedLevel}>
          {#each data.levels as level (level.id)}
            <option value={level.id}>{level.label}</option>
          {/each}
        </select>
      </label>

      <label class="practice-control">
        <span class="practice-control__label">Theme</span>
        <select bind:value={selectedTheme}>
          {#each data.themes as theme (theme.id)}
            <option value={theme.id}>{theme.label}</option>
          {/each}
          <option value={CUSTOM_THEME_ID}>Custom…</option>
        </select>
      </label>

      <label class="practice-control">
        <span class="practice-control__label">Exercise type</span>
        <select bind:value={exerciseType}>
          <option value="sentences">Sentences</option>
          <option value="questions">Questions</option>
          <option value="fill_in_blank">Fill in the blank</option>
          <option value="story">Story</option>
          <option value="vocabulary_candidates">Vocabulary</option>
        </select>
      </label>

      <label class="practice-control">
        <span class="practice-control__label">{isStory ? 'Max sentences' : 'Count'}</span>
        <input type="number" min="1" max="20" bind:value={count} />
      </label>
    </div>

    {#if isCustomTheme}
      <label class="practice-control practice-control--custom-theme">
        <span class="practice-control__label">Custom theme</span>
        <input type="text" placeholder="e.g. Booking a doctor's appointment" bind:value={customThemeText} />
      </label>
    {/if}

    {#if isStory}
      <div class="practice-story-topic">
        <label class="practice-control practice-control--custom-theme">
          <span class="practice-control__label">Story topic</span>
          <input type="text" placeholder="e.g. What did you do last weekend?" bind:value={storyTopic} />
        </label>
        <button type="button" class="secondary practice-story-topic__random" onclick={pickRandomStoryTopic}> Generate random story topic </button>
      </div>
    {/if}

    <div class="practice-toolbar">
      <button type="button" onclick={generate} disabled={loading}>
        {#if loading}
          Generating…
        {:else if isStory}
          Generate model story
        {:else}
          Generate session
        {/if}
      </button>
    </div>

    {#if status}
      <p class="practice-status">{status}</p>
    {/if}
    {#if error}
      <p role="alert">{error}</p>
    {/if}

    {#if isStory}
      <div class="practice-story-panels">
        <div class="practice-panel practice-story-panel">
          <h3>Your story</h3>
          <p class="practice-story-hint">Answer the prompt in first person as a short paragraph.</p>
          <textarea
            class="practice-story-textarea"
            rows="8"
            placeholder="예: 지난 주말에 집에 있었어요. TV를 보고 수학 강의를 준비했어요. 대학에서 수학을 가르치고 싶어요…"
            bind:value={userStory}
          ></textarea>
          <div class="practice-toolbar">
            <button type="button" onclick={evaluateStory} disabled={storyEvaluating || !session?.story || !userStory.trim()}>
              {storyEvaluating ? 'Evaluating…' : 'Evaluate'}
            </button>
          </div>
          {#if storyFeedback}
            <div class="practice-item-reveal">
              <p class="practice-story-feedback">{storyFeedback}</p>
            </div>
          {/if}
        </div>

        {#if session?.story && resultType === 'story'}
          <div class="practice-panel practice-story-panel">
            <div class="practice-story-panel__header">
              <h3>Model story</h3>
              <button
                type="button"
                class="secondary"
                onclick={() => {
                  showModelTranslation = !showModelTranslation;
                }}
              >
                {showModelTranslation ? 'Hide translation' : 'Translate'}
              </button>
            </div>
            {#if session.story.title}
              <h4 class="practice-story-model-title">{session.story.title}</h4>
            {/if}
            <p class="practice-story-paragraph">
              {session.story.sentences.map((sentence) => sentence.hangul).join(' ')}
            </p>
            {#if showModelTranslation}
              {@const translation = session.story.sentences
                .map((sentence) => sentence.english.trim())
                .filter(Boolean)
                .join(' ')}
              {#if translation}
                <p class="practice-story-paragraph practice-story-paragraph--translation">
                  {translation}
                </p>
              {:else}
                <p class="practice-story-paragraph practice-story-paragraph--translation">No English translation was returned for this story. Try generating again.</p>
              {/if}
            {/if}
          </div>
        {/if}
      </div>
    {:else if session && resultType}
      {#if resultType === 'sentences'}
        <div class="practice-panel">
          <ol class="practice-list practice-list--interactive">
            {#each session.sentences ?? [] as sentence, index}
              <li class="practice-item">
                <div class="practice-item-row">
                  <SpeakButton text={sentence.hangul} label={`Pronounce sentence ${index + 1}`} />
                  <input
                    type="text"
                    class="practice-item-input"
                    placeholder="Write what you hear…"
                    value={answers[index] ?? ''}
                    oninput={(event) => setAnswer(index, event.currentTarget.value)}
                  />
                  <button type="button" class="secondary" onclick={() => revealItem(index)}>Evaluate</button>
                </div>
                {#if revealed[index]}
                  <div class="practice-item-reveal">
                    <strong>{sentence.hangul}</strong>
                    <span class="practice-item-english"> ({sentence.english})</span>
                  </div>
                {/if}
              </li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'questions'}
        <div class="practice-panel">
          <ol class="practice-list practice-list--interactive">
            {#each session.questions ?? [] as item, index}
              {@const promptParts = splitPromptEnglish(item.prompt, item.english)}
              <li class="practice-item">
                <div class="practice-item-prompt-row">
                  <SpeakButton text={promptParts.text} label={`Pronounce question ${index + 1}`} />
                  <p class="practice-item-prompt">{promptParts.text}</p>
                  {#if promptParts.translation}
                    <button type="button" class="secondary practice-btn-sm" onclick={() => togglePromptTranslation(index)}>
                      {promptTranslated[index] ? 'Hide' : 'Translate'}
                    </button>
                  {/if}
                </div>
                {#if promptTranslated[index] && promptParts.translation}
                  <p class="practice-item-prompt-translation">{promptParts.translation}</p>
                {/if}
                <div class="practice-item-row">
                  <input
                    type="text"
                    class="practice-item-input"
                    placeholder="Your answer…"
                    value={answers[index] ?? ''}
                    oninput={(event) => setAnswer(index, event.currentTarget.value)}
                  />
                  <button type="button" class="secondary" onclick={() => revealItem(index)}>Evaluate</button>
                </div>
                {#if revealed[index]}
                  <div class="practice-item-reveal">
                    <strong>{item.answer}</strong>
                  </div>
                {/if}
              </li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'fill_in_blank'}
        <div class="practice-panel">
          <ol class="practice-list practice-list--interactive">
            {#each session.fill_in_blank ?? [] as item, index}
              {@const promptParts = splitPromptEnglish(item.prompt, item.english)}
              <li class="practice-item">
                <div class="practice-item-prompt-row">
                  <SpeakButton text={promptParts.text} label={`Pronounce item ${index + 1}`} />
                  <p class="practice-item-prompt">{promptParts.text}</p>
                  {#if promptParts.translation}
                    <button type="button" class="secondary practice-btn-sm" onclick={() => togglePromptTranslation(index)}>
                      {promptTranslated[index] ? 'Hide' : 'Translate'}
                    </button>
                  {/if}
                </div>
                {#if promptTranslated[index] && promptParts.translation}
                  <p class="practice-item-prompt-translation">{promptParts.translation}</p>
                {/if}
                <div class="practice-item-row">
                  <input
                    type="text"
                    class="practice-item-input"
                    placeholder="Fill the blank…"
                    value={answers[index] ?? ''}
                    oninput={(event) => setAnswer(index, event.currentTarget.value)}
                  />
                  <button type="button" class="secondary" onclick={() => revealItem(index)}>Evaluate</button>
                </div>
                {#if revealed[index]}
                  <div class="practice-item-reveal">
                    <strong>{item.answer}</strong>
                  </div>
                {/if}
              </li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'vocabulary_candidates'}
        <div class="practice-panel">
          <ul class="practice-vocab">
            {#each session.vocabulary_candidates ?? [] as candidate}
              <li class="practice-vocab-row">
                <SpeakButton text={candidate.hangul} label={`Pronounce ${candidate.hangul}`} />
                <span class="practice-vocab-text">{candidate.hangul} <span class="practice-item-english">({candidate.english})</span></span>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    {/if}

    {#if session && resultType && resultType !== 'vocabulary_candidates' && session.vocabulary_candidates && session.vocabulary_candidates.length > 0}
      <div class="practice-candidates-section">
        <h4>Vocabulary</h4>
        <ul class="practice-vocab">
          {#each session.vocabulary_candidates as candidate}
            <li class="practice-vocab-row">
              <SpeakButton text={candidate.hangul} label={`Pronounce ${candidate.hangul}`} />
              <span class="practice-vocab-text">{candidate.hangul} <span class="practice-item-english">({candidate.english})</span></span>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if session}
      <div class="practice-toolbar practice-toolbar--staging">
        <button type="button" class="secondary practice-btn-sm" onclick={exportYaml}>Download YAML</button>
        <button type="button" class="secondary practice-btn-sm" onclick={saveToStaging}>Save to staging</button>
      </div>
    {/if}
  </div>
</AiServiceGate>
