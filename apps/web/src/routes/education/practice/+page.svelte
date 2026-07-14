<script lang="ts">
  import yaml from 'yaml';

  import AiServiceGate from '$lib/components/AiServiceGate.svelte';
  import { generatePracticeSession } from '$lib/practice';
  import { downloadTextFile, normalizePracticeSession, todayIsoDate, type PracticeSessionJson } from '$lib/staging';

  let { data } = $props();

  type Tab = 'sentences' | 'questions' | 'fill_in_blank' | 'story';

  let loading = $state(false);
  let error = $state('');
  let status = $state('');
  let session = $state<PracticeSessionJson | null>(null);
  let tab = $state<Tab>('sentences');

  async function generate() {
    loading = true;
    error = '';
    status = 'Generating session…';

    try {
      session = await generatePracticeSession(data.vocabulary);
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

    const requests = [
      fetch('/api/staging', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: 'exercises', payload: docs.exercises, date }),
      }),
    ];

    if (docs.stories) {
      requests.push(
        fetch('/api/staging', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind: 'stories', payload: docs.stories, date }),
        }),
      );
    }

    if (docs.vocabulary) {
      requests.push(
        fetch('/api/staging', {
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
<p>Generate a daily beginner session from your canonical vocabulary.</p>

<AiServiceGate featureLabel="Practice">
  <div class="practice-app">
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

    {#if session}
      <div class="practice-tabs" role="tablist">
        <button type="button" role="tab" aria-current={tab === 'sentences' ? 'page' : undefined} onclick={() => (tab = 'sentences')}>Sentences</button>
        <button type="button" role="tab" aria-current={tab === 'questions' ? 'page' : undefined} onclick={() => (tab = 'questions')}>Questions</button>
        <button type="button" role="tab" aria-current={tab === 'fill_in_blank' ? 'page' : undefined} onclick={() => (tab = 'fill_in_blank')}>Fill-in-blank</button>
        <button type="button" role="tab" aria-current={tab === 'story' ? 'page' : undefined} onclick={() => (tab = 'story')}>Story</button>
      </div>

      <div class="practice-panel">
        {#if tab === 'sentences'}
          <ol class="practice-list">
            {#each session.sentences ?? [] as sentence}
              <li><strong>{sentence.hangul}</strong> — {sentence.english}</li>
            {/each}
          </ol>
        {:else if tab === 'questions'}
          <ol class="practice-list">
            {#each session.questions ?? [] as item}
              <li>{item.question}<br /><em>{item.answer}</em></li>
            {/each}
          </ol>
        {:else if tab === 'fill_in_blank'}
          <ol class="practice-list">
            {#each session.fill_in_blank ?? [] as item}
              <li>{item.sentence.replace(item.blank, '___')}<br /><em>{item.answer}</em> — {item.english}</li>
            {/each}
          </ol>
        {:else}
          {#if session.story?.title}
            <h3>{session.story.title}</h3>
          {/if}
          <ol class="practice-list">
            {#each session.story?.sentences ?? [] as sentence}
              <li><strong>{sentence.hangul}</strong> — {sentence.english}</li>
            {/each}
          </ol>
        {/if}
      </div>
    {/if}
  </div>
</AiServiceGate>
