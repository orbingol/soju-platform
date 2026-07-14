<script lang="ts">
  import { speak } from '$lib/tts';

  interface Props {
    text: string;
    label?: string;
    className?: string;
  }

  let { text, label, className = 'spk' }: Props = $props();

  let speaking = $state(false);
  let btn: HTMLButtonElement | undefined = $state();

  function onClick(event: MouseEvent) {
    event.stopPropagation();
    speaking = true;
    speak(text, btn ?? null);
    // speaking class cleared by tts module on end
    setTimeout(() => {
      speaking = false;
    }, 100);
  }
</script>

<button bind:this={btn} type="button" class="{className}{speaking ? ' speaking' : ''}" data-text={text} aria-label={label ?? `Pronounce ${text}`} onclick={onClick}></button>
