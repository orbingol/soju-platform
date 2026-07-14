<script lang="ts">
  import VocabularyTable from '$lib/components/VocabularyTable.svelte';
  import type { ResolvedEntry, DefaultTableLayout } from '$lib/data/types';

  let { data } = $props();
</script>

<svelte:head>
  <title>{data.type.label} · Education · Soju (소주)</title>
</svelte:head>

<h1>{data.type.label}</h1>

<VocabularyTable mode="default" table={data.table as DefaultTableLayout} entries={data.entries as ResolvedEntry[]} />
