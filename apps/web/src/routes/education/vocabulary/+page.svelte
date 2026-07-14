<script lang="ts">
  import { wordTypesHref, topicsHref, grammarHref } from '$lib/education-nav';
</script>

<svelte:head>
  <title>Vocabulary · Education · Soju (소주)</title>
</svelte:head>

<h1>Vocabulary</h1>
<p>Korean vocabulary for study and reference.</p>
<p>
  <a href={wordTypesHref}>Word types →</a><br />
  <a href={grammarHref}>Grammar →</a><br />
  <a href={topicsHref}>Topics →</a>
</p>
