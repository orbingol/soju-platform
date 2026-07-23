<script lang="ts">
  import { onMount } from 'svelte';
  import type { Snippet } from 'svelte';

  import { aiOfflineMessage, probeAiAvailability } from '$lib/ai/availability';
  import { aiEnabled, sojuApiBaseUrl } from '$lib/config';

  interface Props {
    featureLabel?: string;
    children: Snippet;
  }

  let { featureLabel = 'This feature', children }: Props = $props();

  let checking = $state(aiEnabled);
  let available = $state(false);

  onMount(async () => {
    const result = await probeAiAvailability(aiEnabled);
    checking = result.checking;
    available = result.available;
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
    {aiOfflineMessage(featureLabel, sojuApiBaseUrl)}
  </p>
{:else if ready}
  {@render children()}
{/if}
