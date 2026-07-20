<script lang="ts">
  import { untrack } from 'svelte';
  import yaml from 'yaml';

  import { base } from '$app/paths';

  import AiServiceGate from '$lib/components/AiServiceGate.svelte';
  import { generatePracticeSession, type PracticeExerciseType } from '$lib/practice';
  import { fetchRetrieval } from '$lib/practice/client';
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

  const isCustomTheme = $derived(selectedTheme === CUSTOM_THEME_ID);

  async function generate() {
    error = '';
    status = '';

    const level = data.levels.find((entry) => entry.id === selectedLevel);
    if (!level) {
      error = `Unknown level ${selectedLevel}`;
      return;
    }

    let themeText: string;
    if (isCustomTheme) {
      themeText = customThemeText.trim();
      if (!themeText) {
        error = 'Enter a custom theme description first.';
        return;
      }
    } else {
      const theme = data.themes.find((entry) => entry.id === selectedTheme);
      if (!theme) {
        error = `Unknown theme ${selectedTheme}`;
        return;
      }
      themeText = theme.description;
    }

    loading = true;
    try {
      status = 'Embedding theme…';
      const queryVector = await embedQueryText(themeText);

      status = 'Retrieving vocabulary and grammar…';
      const retrieved = await fetchRetrieval(selectedLevel, queryVector);

      status = 'Generating session…';
      session = await generatePracticeSession({
        level: { label: level.label, guidance: level.guidance, grammarSummary: level.grammarSummary },
        themeText,
        exerciseType,
        count,
        hangul: retrieved.hangul,
        grammar: retrieved.grammar,
      });
      resultType = exerciseType;
      status = 'Session ready.';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Generation failed';
      status = '';
    } finally {
      loading = false;
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

    const stagingUrl = `${base}/api/staging`;
    const requests = [
      fetch(stagingUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: 'exercises', payload: docs.exercises, date }),
      }),
    ];

    if (docs.stories) {
      requests.push(
        fetch(stagingUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind: 'stories', payload: docs.stories, date }),
        }),
      );
    }

    if (docs.vocabulary) {
      requests.push(
        fetch(stagingUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind: 'vocabulary', payload: docs.vocabulary }),
        }),
      );
    }

    try {
      const responses = await Promise.all(requests);
      const failed = responses.find((response) => !response.ok);
      if (failed) {
        const body = await failed.json().catch(() => ({}));
        throw new Error((body as { error?: string }).error ?? 'Save failed');
      }
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
          <option value="vocabulary_candidates">Vocabulary candidates</option>
        </select>
      </label>

      <label class="practice-control">
        <span class="practice-control__label">Count</span>
        <input type="number" min="1" max="20" bind:value={count} />
      </label>
    </div>

    {#if isCustomTheme}
      <label class="practice-control practice-control--custom-theme">
        <span class="practice-control__label">Custom theme</span>
        <input type="text" placeholder="e.g. Booking a doctor's appointment" bind:value={customThemeText} />
      </label>
    {/if}

    <div class="practice-toolbar">
      <button type="button" onclick={generate} disabled={loading}>
        {loading ? 'Generating…' : 'Generate session'}
      </button>
      {#if session}
        <button type="button" class="secondary" onclick={exportYaml}>Download YAML</button>
        <button type="button" class="secondary" onclick={saveToStaging}>Save to staging</button>
      {/if}
    </div>

    {#if status}
      <p class="practice-status">{status}</p>
    {/if}
    {#if error}
      <p role="alert">{error}</p>
    {/if}

    {#if session && resultType}
      {#if resultType === 'sentences'}
        <div class="practice-panel">
          <ol class="practice-list">
            {#each session.sentences ?? [] as sentence}
              <li><strong>{sentence.hangul}</strong> — {sentence.english}</li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'questions'}
        <div class="practice-panel">
          <ol class="practice-list">
            {#each session.questions ?? [] as item}
              <li>{item.question}<br /><em>{item.answer}</em></li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'fill_in_blank'}
        <div class="practice-panel">
          <ol class="practice-list">
            {#each session.fill_in_blank ?? [] as item}
              <li>{item.sentence.replace(item.blank, '___')}<br /><em>{item.answer}</em> — {item.english}</li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'story'}
        <div class="practice-panel">
          {#if session.story?.title}
            <h3>{session.story.title}</h3>
          {/if}
          <ol class="practice-list">
            {#each session.story?.sentences ?? [] as sentence}
              <li><strong>{sentence.hangul}</strong> — {sentence.english}</li>
            {/each}
          </ol>
        </div>
      {:else if resultType === 'vocabulary_candidates'}
        <div class="practice-panel">
          <ul class="practice-candidates">
            {#each session.vocabulary_candidates ?? [] as candidate}
              <li><strong>{candidate.hangul}</strong> — {candidate.english}</li>
            {/each}
          </ul>
        </div>
      {/if}

      {#if resultType !== 'vocabulary_candidates' && session.vocabulary_candidates && session.vocabulary_candidates.length > 0}
        <div class="practice-candidates-section">
          <h4>Also worth learning</h4>
          <ul class="practice-candidates">
            {#each session.vocabulary_candidates as candidate}
              <li><strong>{candidate.hangul}</strong> — {candidate.english}</li>
            {/each}
          </ul>
        </div>
      {/if}
    {/if}
  </div>
</AiServiceGate>
