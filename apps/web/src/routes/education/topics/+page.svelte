<script lang="ts">
  import { base } from '$app/paths';

  let { data } = $props();
</script>

<svelte:head>
  <title>Topics · Education · Soju (소주)</title>
</svelte:head>

<h1>Topics</h1>
<p>Curated vocabulary sets grouped by theme.</p>

<ul>
  {#each data.topics as topic}
    <li>
      <a href="{base}/education/topics/{topic.id}/">{topic.label}</a>
      {#if topic.description}
        — {topic.description}
      {/if}
    </li>
  {/each}
</ul>
