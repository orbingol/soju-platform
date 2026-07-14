<script lang="ts">
  import SpeakButton from '$lib/components/SpeakButton.svelte';

  interface Props {
    hangul: string;
    romanization: string;
  }

  let { hangul, romanization }: Props = $props();

  let showRom = $state(false);

  function toggleRom(event: MouseEvent) {
    event.stopPropagation();
    showRom = !showRom;
  }
</script>

<div class="root-block">
  <div class="root-top">
    <span class="root-text">{hangul}</span>
    <SpeakButton text={hangul} label={`Pronounce ${hangul}`} />
    <span class="root-tools">
      <button
        type="button"
        class="rom-toggle{showRom ? ' is-active' : ''}"
        aria-label={showRom ? `Hide romanization for ${hangul}` : `Show romanization for ${hangul}`}
        aria-pressed={showRom}
        onclick={toggleRom}
      >
        Aa
      </button>
      {#if showRom}
        <span class="root-rom root-rom--inline">{romanization}</span>
      {/if}
    </span>
  </div>
</div>
