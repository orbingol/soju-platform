<script lang="ts">
  import VocabularyTable from '$lib/components/VocabularyTable.svelte';
  import type { VerbEntry, VerbTableLayout } from '$lib/data/types';

  let { data } = $props();
</script>

<svelte:head>
  <title>Verbs · Education · Soju (소주)</title>
</svelte:head>

<h1>Verbs</h1>

<VocabularyTable mode="verb" table={data.table as VerbTableLayout} verbs={data.entries as VerbEntry[]} />
