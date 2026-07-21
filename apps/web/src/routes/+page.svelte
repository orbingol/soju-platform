<script lang="ts">
  import { base } from '$app/paths';
</script>

<svelte:head>
  <title>Soju (소주)</title>
</svelte:head>

<h1>Soju (소주) Platform</h1>
<p>Soju (소주) Platform provides references and practice tools for your Korean language learning experience.</p>

<section class="platform-sections" aria-label="Platform sections">
  <a class="platform-section-card" href="{base}/education/">
    <span class="platform-section-card__icon" aria-hidden="true">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    </span>
    <h2>Education</h2>
    <p>Korean vocabulary, grammar reference, and study tools. <span class="platform-section-card__cta">Open Education →</span></p>
  </a>
</section>
