<script lang="ts">
  import '../app.css';

  import { base } from '$app/paths';
  import { page } from '$app/stores';

  import Breadcrumb from '$lib/components/Breadcrumb.svelte';
  import type { Crumb } from '$lib/components/breadcrumb';
  import ChatDock from '$lib/components/ChatDock.svelte';
  import EdgePanel from '$lib/components/EdgePanel.svelte';
  import SiteChrome from '$lib/components/SiteChrome.svelte';
  import { buildEducationFallbackCrumbs, buildEducationNavItems, educationHref } from '$lib/education-nav';
  import { aiEnabled } from '$lib/config';

  let { children } = $props();

  const siteTitle = 'Soju (소주)';

  const isEducation = $derived($page.url.pathname.includes('/education'));
  const pathname = $derived($page.url.pathname);
  const section = $derived(pathname.replace(/\/$/, '').split('/').pop() ?? '');

  const navItems = $derived(
    isEducation
      ? buildEducationNavItems(siteTitle, pathname, aiEnabled)
      : [
          { label: siteTitle, href: `${base}/`, current: pathname === `${base}/` || pathname === '/' },
          {
            label: 'Education',
            href: educationHref,
            current: pathname.includes('/education'),
          },
        ],
  );

  const crumbs = $derived.by((): Crumb[] => {
    const fromPage = $page.data.breadcrumbs as Crumb[] | undefined;
    if (fromPage?.length) return fromPage;

    if (!isEducation) {
      return [{ label: 'Home' }];
    }

    const topicLabel = ($page.data.meta as { label?: string } | undefined)?.label ?? section;
    return buildEducationFallbackCrumbs(pathname, section, topicLabel);
  });
</script>

<div class="app-shell">
  {#if isEducation}
    <EdgePanel />
  {/if}

  {#if $page.data.chat}
    <ChatDock chat={$page.data.chat} />
  {/if}

  <div class="app-main">
    <SiteChrome
      {siteTitle}
      sectionTitle={isEducation ? 'Education' : undefined}
      sectionHref={isEducation ? educationHref : undefined}
      navLabel={isEducation ? 'Education' : 'Site'}
      {navItems}
    />
    <Breadcrumb {crumbs} />

    <main class="app-content">
      {@render children()}
    </main>
  </div>
</div>
