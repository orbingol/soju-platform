<script lang="ts">
  import { base } from '$app/paths';

  let { data } = $props();
</script>

<svelte:head>
  <title>Word types · Education · Soju (소주)</title>
</svelte:head>

<h1>Word types</h1>
<p>Browse vocabulary by grammatical type.</p>

<ul>
  {#each data.types as type}
    <li>
      <a href="{base}/education/words/{type.slug}/">{type.label}</a>
    </li>
  {/each}
</ul>
