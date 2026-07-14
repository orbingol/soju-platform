<script lang="ts">
  import type { Example } from '$lib/data/types';
  import SpeakButton from '$lib/components/SpeakButton.svelte';

  interface Props {
    examples: Example[];
  }

  let { examples }: Props = $props();

  let index = $state(0);

  const current = $derived(examples[index] ?? { hangul: '', english: '' });
  const hasMany = $derived(examples.length > 1);

  $effect(() => {
    examples;
    index = 0;
  });

  function prev(event: MouseEvent) {
    event.stopPropagation();
    if (examples.length <= 1) return;
    index = (index - 1 + examples.length) % examples.length;
  }

  function next(event: MouseEvent) {
    event.stopPropagation();
    if (examples.length <= 1) return;
    index = (index + 1) % examples.length;
  }
</script>

<div class="example-cell">
  <div class="example-cell__hangul">
    <span class="tip-h">{current.hangul}</span>
    <SpeakButton text={current.hangul} label="Pronounce example sentence" />
  </div>
  <span class="tip-e">{current.english}</span>
  <span class="tip-counter">{index + 1} / {examples.length}</span>
  {#if hasMany}
    <div class="example-cell__nav">
      <button type="button" class="tip-nav tip-nav--prev" aria-label="Previous example" onclick={prev}> ‹ </button>
      <button type="button" class="tip-nav tip-nav--next" aria-label="Next example" onclick={next}> › </button>
    </div>
  {/if}
</div>
