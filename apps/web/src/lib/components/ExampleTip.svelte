<script lang="ts">
  import { browser } from '$app/environment';

  import type { Example } from '$lib/data/types';
  import { speak } from '$lib/tts';

  interface Props {
    examples: Example[];
    anchor: HTMLElement | null;
    visible: boolean;
    touchMode?: boolean;
    onTipEnter?: () => void;
    onTipLeave?: () => void;
  }

  let { examples, anchor, visible, touchMode = false, onTipEnter, onTipLeave }: Props = $props();

  let tipEl: HTMLDivElement | undefined = $state();
  let index = $state(0);
  let left = $state(0);
  let top = $state(0);

  const current = $derived(examples[index] ?? { hangul: '', english: '' });
  const hasMany = $derived(examples.length > 1);

  function positionTip() {
    if (!browser || !visible || !anchor || !tipEl || touchMode) return;

    const container = tipEl.closest('[data-word-table], [data-verb-table]') as HTMLElement | null;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const formRect = anchor.getBoundingClientRect();

    let nextLeft = formRect.left - containerRect.left + container.scrollLeft;
    let nextTop = formRect.bottom - containerRect.top + container.scrollTop + 6;

    if (nextLeft + tipEl.offsetWidth > container.clientWidth) {
      nextLeft = container.clientWidth - tipEl.offsetWidth;
    }
    if (nextLeft < 0) nextLeft = 0;

    left = nextLeft;
    top = nextTop;
  }

  $effect(() => {
    if (!browser || !visible || !anchor || !tipEl) return;

    if (touchMode) {
      left = 0;
      top = 0;
      return;
    }

    positionTip();
    requestAnimationFrame(positionTip);
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

  function speakExample(event: MouseEvent) {
    event.stopPropagation();
    speak(current.hangul);
  }

  export function resetIndex() {
    index = 0;
  }
</script>

<div
  bind:this={tipEl}
  class="verb-tip{touchMode ? ' verb-tip--touch' : ''}"
  role="tooltip"
  aria-hidden={!visible}
  style:display={visible ? 'flex' : 'none'}
  style:left={touchMode ? undefined : `${left}px`}
  style:top={touchMode ? undefined : `${top}px`}
  onmouseenter={onTipEnter}
  onmouseleave={onTipLeave}
>
  <button type="button" class="tip-nav tip-nav--prev" aria-label="Previous example" hidden={!hasMany} onclick={prev}> ‹ </button>
  <div class="tip-main">
    <div class="tip-row">
      <span class="tip-h">{current.hangul}</span>
      <button type="button" class="spk tip-spk" aria-label="Pronounce example sentence" onclick={speakExample}></button>
    </div>
    <span class="tip-e">{current.english}</span>
    {#if hasMany}
      <span class="tip-counter">{index + 1} / {examples.length}</span>
    {/if}
  </div>
  <button type="button" class="tip-nav tip-nav--next" aria-label="Next example" hidden={!hasMany} onclick={next}> › </button>
</div>
