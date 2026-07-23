<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  import type { ConjugationColumn, DefaultTableLayout, Example, ResolvedEntry, TopicSection, VerbEntry, VerbTableLayout } from '$lib/data/types';
  import { matchesVocabularySearch, resolveVerbCell } from '$lib/data/loader';
  import { sanitizeHtml } from '$lib/sanitize-html';
  import ExampleCell from '$lib/components/ExampleCell.svelte';
  import RootCell from '$lib/components/RootCell.svelte';
  import SpeakButton from '$lib/components/SpeakButton.svelte';
  import TableSearch from '$lib/components/TableSearch.svelte';
  import { bindSpeakButtons, isTtsAvailable, showNoTtsBanner } from '$lib/tts';

  type Mode = 'verb' | 'default' | 'topic';

  interface Props {
    mode: Mode;
    table: VerbTableLayout | DefaultTableLayout;
    verbs?: VerbEntry[];
    entries?: ResolvedEntry[];
    sections?: TopicSection[];
  }

  let { mode, table, verbs = [], entries = [], sections = [] }: Props = $props();

  let wrapper: HTMLDivElement | undefined = $state();
  let searchQuery = $state('');
  let expandedVerbs = $state<Set<string>>(new Set());

  const verbTable = $derived(mode === 'verb' ? (table as VerbTableLayout) : null);
  const defaultTable = $derived(mode !== 'verb' ? (table as DefaultTableLayout) : null);
  const examplesLabel = $derived(defaultTable?.examples?.label ?? 'Examples');

  const filteredVerbs = $derived(verbs.filter((verb) => matchesVocabularySearch(verb, searchQuery)));

  const filteredEntries = $derived(entries.filter((entry) => matchesVocabularySearch(entry, searchQuery)));

  const filteredSections = $derived(
    sections
      .map((section) => ({
        ...section,
        entries: section.entries.filter((entry) => matchesVocabularySearch(entry, searchQuery)),
      }))
      .filter((section) => section.entries.length > 0 || section.description || !searchQuery.trim()),
  );

  const colCount = $derived(verbTable ? 2 + verbTable.sections.reduce((sum, section) => sum + section.columns.length, 0) : 0);

  const hasExamples = $derived(
    mode === 'topic'
      ? sections.some((s) => s.entries.some((e) => (e.examples?.length ?? 0) > 0))
      : mode === 'default'
        ? filteredEntries.some((e) => (e.examples?.length ?? 0) > 0)
        : false,
  );

  function cellData(verb: VerbEntry, sectionId: string, column: ConjugationColumn) {
    return resolveVerbCell(verb, sectionId, column);
  }

  function isExpanded(verb: VerbEntry): boolean {
    return expandedVerbs.has(verb.id);
  }

  function toggleVerb(verb: VerbEntry) {
    const next = new Set(expandedVerbs);
    if (next.has(verb.id)) {
      next.delete(verb.id);
    } else {
      next.add(verb.id);
    }
    expandedVerbs = next;
  }

  function onFormActivate(verb: VerbEntry, examples: Example[]) {
    if (examples.length === 0) return;
    toggleVerb(verb);
  }

  onMount(() => {
    if (!browser || !wrapper) return;
    bindSpeakButtons(wrapper);
    showNoTtsBanner(wrapper);
  });
</script>

<p class="hint">
  Click any <span class="icon-volume" aria-hidden="true"></span> to hear pronunciation
  {#if mode === 'verb'}
    · click a conjugated form to show example sentences
  {/if}
</p>

<p class="verb-no-tts" hidden={browser ? isTtsAvailable() : true}>
  <span class="icon-alert" aria-hidden="true"></span>
  Speech is unavailable (no local TTS service and no Web Speech API). Speaker buttons are hidden.
</p>

<div bind:this={wrapper} data-vocab-table class:no-tts={browser && !isTtsAvailable()}>
  <div class="table-toolbar">
    <TableSearch bind:value={searchQuery} />
  </div>

  {#if mode === 'verb' && verbTable}
    {@const tenseColCount = verbTable.sections.reduce((sum, section) => sum + section.columns.length, 0)}
    <section class="table-section">
      <div class="table-wrap">
        <table class="verb-table verb-table--unified">
          <thead>
            <tr>
              <th rowspan="2" class="root-col">
                {verbTable.fields.hangul.label}
                {#if verbTable.fields.hangul.subtitle}
                  <br /><span class="col-sub">{verbTable.fields.hangul.subtitle}</span>
                {/if}
              </th>
              <th rowspan="2" class="meaning-col">
                {verbTable.fields.english.label}
                {#if verbTable.fields.english.subtitle}
                  <br /><span class="col-sub">{verbTable.fields.english.subtitle}</span>
                {/if}
              </th>
              {#each verbTable.sections as section (section.id)}
                <th colspan={section.columns.length} class={section.css}>{section.label}</th>
              {/each}
            </tr>
            <tr>
              {#each verbTable.sections as section (section.id)}
                {#each section.columns as column}
                  <th class={section.css}>
                    {column.label}<br /><span class="col-sub">{column.subtitle}</span>
                  </th>
                {/each}
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each filteredVerbs as verb (verb.id)}
              {@const expanded = isExpanded(verb)}
              <tr class:verb-row--has-panel={expanded}>
                <td class="root-cell">
                  <RootCell hangul={verb.hangul} romanization={verb.romanization} />
                </td>
                <td class="meaning">{verb.english}</td>
                {#each verbTable.sections as section (section.id)}
                  {#each section.columns as column}
                    {@const cell = cellData(verb, section.id, column)}
                    <td class={section.css}>
                      <span class="vf-wrap">
                        {#if cell.examples.length > 0}
                          <span
                            class="vf"
                            class:is-expanded={expanded}
                            role="button"
                            tabindex="0"
                            aria-expanded={expanded}
                            aria-label="Show examples for {cell.form}"
                            onclick={(event) => {
                              event.stopPropagation();
                              onFormActivate(verb, cell.examples);
                            }}
                            onkeydown={(event) => {
                              if (event.key !== 'Enter' && event.key !== ' ') return;
                              event.preventDefault();
                              onFormActivate(verb, cell.examples);
                            }}
                          >
                            {cell.form}
                          </span>
                        {:else}
                          <span class="form-text">{cell.form}</span>
                        {/if}
                        <SpeakButton text={cell.form} label={`Pronounce ${cell.form}`} />
                      </span>
                    </td>
                  {/each}
                {/each}
              </tr>
              {#if expanded}
                <tr class="verb-example-row">
                  <td colspan={2 + tenseColCount}>
                    <div class="verb-example-panel">
                      <div class="verb-example-tense-grid" style:--tenses={verbTable.sections.length}>
                        {#each verbTable.sections as section (section.id)}
                          <div class="verb-example-tense-group {section.css}">
                            <div class="verb-example-tense-label">{section.label}</div>
                            <div class="verb-example-group-grid" style:--cols={section.columns.length}>
                              {#each section.columns as column, columnIndex}
                                {@const cell = cellData(verb, section.id, column)}
                                <div class="verb-example-cell {section.css}" class:verb-example-cell--bordered={columnIndex > 0}>
                                  {#if cell.examples.length > 0}
                                    <span class="verb-example-form">{cell.form}</span>
                                    <ExampleCell examples={cell.examples} />
                                  {/if}
                                </div>
                              {/each}
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  {:else if mode === 'default' && defaultTable}
    <div class="table-wrap">
      <table class="verb-table word-table">
        <thead>
          <tr>
            <th class="root-col">{defaultTable.fields.hangul.label}</th>
            <th class="meaning-col">{defaultTable.fields.english.label}</th>
            {#if hasExamples}
              <th class="examples-col">{examplesLabel}</th>
            {/if}
          </tr>
        </thead>
        <tbody>
          {#each filteredEntries as entry (entry.id)}
            {@const examples = entry.examples ?? []}
            <tr>
              <td class="root-cell">
                <RootCell hangul={entry.hangul} romanization={entry.romanization} />
              </td>
              <td class="meaning">{entry.english}</td>
              {#if hasExamples}
                <td class="examples-cell">
                  {#if examples.length > 0}
                    <ExampleCell {examples} />
                  {/if}
                </td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else if mode === 'topic' && defaultTable}
    {#each filteredSections as section (section.id)}
      {#if section.entries.length > 0 || section.description}
        <section class="table-section">
          <h2>{section.label}</h2>
          {#if section.description}
            <div class="section-description">{@html sanitizeHtml(section.description)}</div>
          {/if}
          {#if section.entries.length > 0}
            <div class="table-wrap">
              <table class="verb-table word-table">
                <thead>
                  <tr>
                    <th class="root-col">{defaultTable.fields.hangul.label}</th>
                    <th class="meaning-col">{defaultTable.fields.english.label}</th>
                    {#if hasExamples}
                      <th class="examples-col">{examplesLabel}</th>
                    {/if}
                  </tr>
                </thead>
                <tbody>
                  {#each section.entries as entry (entry.id)}
                    {@const examples = entry.examples ?? []}
                    <tr>
                      <td class="root-cell">
                        <RootCell hangul={entry.hangul} romanization={entry.romanization} />
                      </td>
                      <td class="meaning">{entry.english}</td>
                      {#if hasExamples}
                        <td class="examples-cell">
                          {#if examples.length > 0}
                            <ExampleCell {examples} />
                          {/if}
                        </td>
                      {/if}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </section>
      {/if}
    {/each}
  {/if}
</div>
