<script lang="ts">
  import { base } from '$app/paths';

  import GrammarConversation from '$lib/components/GrammarConversation.svelte';

  let { data } = $props();

  const pageTitle = $derived(
    data.mode === 'category' && data.category
      ? `${data.category.label} · Grammar · Soju (소주)`
      : data.mode === 'pattern' && data.page
        ? `${data.page.form} · Grammar · Soju (소주)`
        : 'Grammar · Soju (소주)',
  );
</script>

<svelte:head>
  <title>{pageTitle}</title>
</svelte:head>

{#if data.mode === 'category' && data.category}
  <header class="grammar-hero">
    <h1 class="grammar-title">
      {data.category.label}
      <a class="grammar-back-inline" href="{base}/education/grammar/">(Back to Grammar)</a>
    </h1>
    <p class="grammar-summary">{data.category.description}</p>
  </header>

  <ul class="grammar-index-list">
    {#each data.patterns ?? [] as pattern (pattern.id)}
      <li>
        <a href="{base}/education/grammar/{pattern.id}/">
          <span class="grammar-form">{pattern.form}</span>
          <span class="grammar-english">{pattern.english}</span>
        </a>
        {#if pattern.description}
          <p class="grammar-blurb">{pattern.description}</p>
        {/if}
      </li>
    {/each}
  </ul>
{:else if data.mode === 'pattern' && data.page}
  {@const page = data.page}

  <header class="grammar-hero">
    <h1 class="grammar-title">
      {page.form}
      {#if data.category}
        <a class="grammar-back-inline" href="{base}/education/grammar/{data.category.slug}/">(Back to {data.category.label})</a>
      {:else}
        <a class="grammar-back-inline" href="{base}/education/grammar/">(Back to Grammar)</a>
      {/if}
    </h1>
    <p class="grammar-subtitle">{page.english}</p>
    <p class="grammar-romanization">{page.romanization}</p>
    <p class="grammar-summary">{page.summary}</p>
  </header>

  {#if page.notes?.length}
    <section class="grammar-notes">
      <h2>Notes</h2>
      <ul>
        {#each page.notes as note}
          <li>{note}</li>
        {/each}
      </ul>
    </section>
  {/if}

  {#each page.sections as section (section.id)}
    <section class="grammar-section">
      <h2>{section.label}</h2>
      {#if section.description}
        <p class="grammar-section-desc">{section.description}</p>
      {/if}
      <ul class="grammar-examples">
        {#each section.examples as example}
          <li>
            <div class="grammar-ex-hangul">{example.hangul}</div>
            <div class="grammar-ex-english">{example.english}</div>
          </li>
        {/each}
      </ul>
    </section>
  {/each}

  {#if page.conversations?.length}
    <section class="grammar-conversations">
      <h2>Conversations</h2>
      <p class="grammar-section-desc">Read the Korean first. Tap EN to check the translation.</p>
      {#each page.conversations as conversation}
        <GrammarConversation {conversation} />
      {/each}
    </section>
  {/if}
{/if}
