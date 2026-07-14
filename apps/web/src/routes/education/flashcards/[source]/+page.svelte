<script lang="ts">
  import FlashcardDeck from '$lib/components/FlashcardDeck.svelte';

  let { data } = $props();
</script>

<svelte:head>
  <title>Flashcards · Education · Soju (소주)</title>
</svelte:head>

<h1>Flashcards</h1>

<FlashcardDeck cards={data.cards} source={data.source} topics={data.topics} />
