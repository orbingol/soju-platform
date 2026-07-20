<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';

  import {
    buildDeckKey,
    createProgress,
    filterDeck,
    filterStillLearning,
    FLASHCARDS_PROGRESS_CLEARED,
    loadProgress,
    markCard,
    saveProgress,
    shuffle,
    type Flashcard,
    type FlashcardProgress,
  } from '$lib/flashcards';
  import type { TopicMeta } from '$lib/data/types';
  import SpeakButton from '$lib/components/SpeakButton.svelte';

  interface Props {
    cards: Flashcard[];
    source: string;
    topics: TopicMeta[];
  }

  let { cards, source, topics }: Props = $props();

  let shuffled = $state<Flashcard[]>([]);
  let progress = $state<FlashcardProgress | null>(null);
  let index = $state(0);
  let flipped = $state(false);
  let unknownOnly = $state(false);

  const deckKey = $derived(buildDeckKey(source, unknownOnly));
  const current = $derived(shuffled[index] ?? null);
  const total = $derived(shuffled.length);

  async function persistIndex(nextIndex: number) {
    if (!progress) return;
    progress = { ...progress, index: nextIndex };
    await saveProgress(progress);
  }

  async function initDeck() {
    progress = await loadProgress();
    if (!progress || progress.deckKey !== deckKey) {
      progress = createProgress(deckKey);
      await saveProgress(progress);
    }

    const baseCards = filterDeck(cards, unknownOnly, progress);
    shuffled = shuffle(baseCards);
    index = Math.min(progress.index, Math.max(shuffled.length - 1, 0));
    flipped = false;
  }

  $effect(() => {
    deckKey;
    cards;
    void initDeck();
  });

  onMount(() => {
    const onProgressCleared = () => {
      void initDeck();
    };
    window.addEventListener(FLASHCARDS_PROGRESS_CLEARED, onProgressCleared);
    return () => window.removeEventListener(FLASHCARDS_PROGRESS_CLEARED, onProgressCleared);
  });

  async function nextCard(known: boolean) {
    if (!current || !progress) return;

    progress = await markCard(progress, current.id, known);
    flipped = false;

    if (index < shuffled.length - 1) {
      await persistIndex(index + 1);
      index += 1;
      return;
    }

    await persistIndex(0);
    shuffled = shuffle(filterDeck(cards, unknownOnly, progress));
    index = 0;
  }

  function toggleFlip() {
    flipped = !flipped;
  }

  async function browsePrev() {
    if (index <= 0) return;
    index -= 1;
    flipped = false;
    await persistIndex(index);
  }

  async function browseNext() {
    if (index >= shuffled.length - 1) return;
    index += 1;
    flipped = false;
    await persistIndex(index);
  }

  async function reshuffle() {
    const pool = filterStillLearning(cards, progress);
    if (pool.length === 0) {
      shuffled = [];
      index = 0;
      flipped = false;
      return;
    }

    shuffled = shuffle(pool);
    index = 0;
    flipped = false;
    await persistIndex(0);
  }

  function changeSource(nextSource: string) {
    window.location.href = `${base}/education/flashcards/${nextSource}/`;
  }
</script>

<div class="flashcard-app">
  {#if total === 0}
    <p class="flashcard-empty">No cards in this deck. Try turning off “Practice unknown only”, shuffle still-learning cards, or pick another source.</p>
  {:else if current}
    <p class="flashcard-meta">Card {index + 1} of {total}</p>

    <div class="flashcard-stage">
      <div
        class="flashcard{flipped ? ' is-flipped' : ''}"
        onclick={toggleFlip}
        onkeydown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            toggleFlip();
          }
        }}
        role="button"
        tabindex="0"
        aria-label="Flip card"
      >
        <div class="flashcard-face flashcard-face--front">
          <div class="flashcard-hangul">{current.hangul}</div>
          <SpeakButton text={current.hangul} label={`Pronounce ${current.hangul}`} />
          <span class="flashcard-hint">Tap to reveal</span>
        </div>
        <div class="flashcard-face flashcard-face--back">
          <div class="flashcard-english">{current.english}</div>
          <span class="flashcard-back-meta">{current.hangul}</span>
        </div>
      </div>
    </div>

    <nav class="flashcard-nav" aria-label="Flashcard controls">
      <button type="button" class="secondary outline" disabled={index === 0} onclick={browsePrev}>‹ Prev</button>
      <button type="button" class="secondary" onclick={() => nextCard(false)}>Still learning</button>
      <button type="button" onclick={() => nextCard(true)}>Known</button>
      <button type="button" class="secondary outline" disabled={index >= total - 1} onclick={browseNext}> Next › </button>
    </nav>

    <div class="flashcard-controls">
      <label class="flashcard-control flashcard-control--source">
        <span class="flashcard-control__label">Deck source</span>
        <select value={source} onchange={(event) => changeSource(event.currentTarget.value)}>
          <option value="registry">All registry words</option>
          {#each topics as topic}
            <option value={topic.id}>{topic.label}</option>
          {/each}
        </select>
      </label>

      <label class="flashcard-control flashcard-control--checkbox">
        <input type="checkbox" bind:checked={unknownOnly} />
        Practice unknown only
      </label>

      <button type="button" class="secondary" onclick={reshuffle}>Shuffle</button>
    </div>
  {/if}
</div>
