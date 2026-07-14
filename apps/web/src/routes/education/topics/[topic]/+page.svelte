<script lang="ts">
  import VocabularyTable from '$lib/components/VocabularyTable.svelte';
  import type { DefaultTableLayout, TopicSection } from '$lib/data/types';

  let { data } = $props();
</script>

<svelte:head>
  <title>{data.meta.label} · Topics · Soju (소주)</title>
</svelte:head>

<h1>{data.meta.label}</h1>
{#if data.meta.description}
  <p>{data.meta.description}</p>
{/if}

<VocabularyTable mode="topic" table={data.table as DefaultTableLayout} sections={data.sections as TopicSection[]} />
