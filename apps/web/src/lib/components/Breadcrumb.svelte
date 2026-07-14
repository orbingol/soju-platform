<script lang="ts">
  import { base } from '$app/paths';

  import type { Crumb } from '$lib/components/breadcrumb';

  interface Props {
    crumbs: Crumb[];
  }

  let { crumbs }: Props = $props();
</script>

<nav class="site-breadcrumb" aria-label="Breadcrumb">
  <ol>
    {#each crumbs as crumb, index}
      <li aria-current={index === crumbs.length - 1 ? 'page' : undefined}>
        {#if crumb.href && index < crumbs.length - 1}
          <a href={crumb.href}>{crumb.label}</a>
        {:else}
          {crumb.label}
        {/if}
      </li>
    {/each}
  </ol>
</nav>
