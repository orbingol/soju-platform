<script lang="ts">
  import { aiEnabled } from '$lib/config';
  import { flashcardsHref, practiceHref, vocabularyHref } from '$lib/education-nav';
</script>

<svelte:head>
  <title>Education · Soju (소주)</title>
</svelte:head>

<h1>Soju (소주) Education</h1>
<p>Look things up. Flip cards. Practice for real — all in one place.</p>

<section class="platform-sections" aria-label="Education sections">
  <a class="platform-section-card" href={vocabularyHref}>
    <span class="platform-section-card__icon" aria-hidden="true">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    </span>
    <h2>Vocabulary</h2>
    <p>Word types, grammar patterns, and topics for study and reference. <span class="platform-section-card__cta">Open Vocabulary →</span></p>
  </a>

  <a class="platform-section-card" href={flashcardsHref}>
    <span class="platform-section-card__icon" aria-hidden="true">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z" />
        <path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" />
        <path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" />
      </svg>
    </span>
    <h2>Flashcards</h2>
    <p>Flip through Hangul and English to drill vocabulary. <span class="platform-section-card__cta">Open Flashcards →</span></p>
  </a>

  {#if aiEnabled}
    <a class="platform-section-card" href={practiceHref}>
      <span class="platform-section-card__icon" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20h9" />
          <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506L2.5 20.5l1.359-3.999a2 2 0 0 1 .506-.855z" />
        </svg>
      </span>
      <h2>Practice</h2>
      <p>AI-guided practice that helps you use Korean, not just memorize it. <span class="platform-section-card__cta">Open Practice →</span></p>
    </a>
  {/if}
</section>
