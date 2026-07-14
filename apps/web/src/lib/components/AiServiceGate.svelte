<script lang="ts">
  import { onMount } from 'svelte';
  import type { Snippet } from 'svelte';

  import { checkAiAvailable } from '$lib/ai/client';
  import { aiBaseUrl, aiEnabled } from '$lib/config';

  interface Props {
    featureLabel?: string;
    children: Snippet;
  }

  let { featureLabel = 'This feature', children }: Props = $props();

  let checking = $state(aiEnabled);
  let available = $state(false);

  onMount(async () => {
    if (!aiEnabled) {
      checking = false;
      return;
    }

    available = await checkAiAvailable();
    checking = false;
  });

  const disabled = $derived(!aiEnabled);
  const offline = $derived(aiEnabled && !checking && !available);
  const ready = $derived(aiEnabled && !checking && available);
</script>

{#if disabled}
  <p class="ai-status ai-status--disabled" role="status">
    {featureLabel} is not available in this deployment.
  </p>
{:else if checking}
  <p class="ai-status" role="status">Checking language model service…</p>
{:else if offline}
  <p class="ai-status ai-status--offline" role="status">
    {featureLabel} is unavailable at <code>{aiBaseUrl}</code>. Confirm the model service is running, CORS allows
    <code>{typeof window !== 'undefined' ? window.location.origin : 'this site'}</code>, then reload.
  </p>
{:else if ready}
  {@render children()}
{/if}
