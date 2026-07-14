<script lang="ts">
  import { base } from '$app/paths';

  let { data } = $props();
</script>

<svelte:head>
  <title>Grammar · Education · Soju (소주)</title>
</svelte:head>

<h1>Grammar</h1>
<p>Patterns that glue Korean sentences together — not dictionary words, but the small pieces that show relationships, time, requests, and questions.</p>

<section class="grammar-category-cards">
  {#each data.categories as category (category.id)}
    <a class="grammar-category-card" href="{base}/education/grammar/{category.slug}/">
      <h2>{category.label}</h2>
      <p>{category.description}</p>
      <span class="grammar-category-card-cta">Browse {category.label.toLowerCase()} →</span>
    </a>
  {/each}
</section>
