<script lang="ts">
  import type { GrammarConversation } from '$lib/data/types';

  interface Props {
    conversation: GrammarConversation;
  }

  let { conversation }: Props = $props();

  let openTurns = $state<Set<number>>(new Set());

  const allOpen = $derived(conversation.turns.length > 0 && openTurns.size === conversation.turns.length);

  function toggle(index: number) {
    const next = new Set(openTurns);
    if (next.has(index)) next.delete(index);
    else next.add(index);
    openTurns = next;
  }

  function toggleAll() {
    openTurns = allOpen ? new Set() : new Set(conversation.turns.map((_, i) => i));
  }
</script>

<article class="grammar-dialogue">
  <div class="grammar-dialogue-header">
    <h3>{conversation.title}</h3>
    <button type="button" class="grammar-translate-btn" onclick={toggleAll}>
      {allOpen ? 'Hide all' : 'Show all'}
    </button>
  </div>

  <ol class="grammar-turns">
    {#each conversation.turns as turn, index}
      {@const open = openTurns.has(index)}
      <li class="grammar-turn" class:grammar-turn--open={open}>
        <div class="grammar-turn-row">
          <span class="grammar-speaker">{turn.speaker}:</span>
          <div class="grammar-turn-body">
            <div class="grammar-ex-hangul">{turn.hangul}</div>
            {#if open}
              <div class="grammar-ex-english">{turn.english}</div>
            {/if}
          </div>
          <button type="button" class="grammar-translate-btn" aria-expanded={open} aria-label={open ? 'Hide translation' : 'Show translation'} onclick={() => toggle(index)}>
            {open ? 'Hide' : 'EN'}
          </button>
        </div>
      </li>
    {/each}
  </ol>
</article>
