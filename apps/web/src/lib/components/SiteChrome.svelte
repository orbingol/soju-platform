<script lang="ts">
  import { base } from '$app/paths';

  import type { NavItem } from '$lib/nav';

  interface Props {
    siteTitle?: string;
    sectionTitle?: string;
    sectionHref?: string;
    navLabel?: string;
    navItems?: NavItem[];
  }

  let { siteTitle = 'Soju (소주)', sectionTitle, sectionHref, navLabel = 'Site', navItems = [] }: Props = $props();

  const homeHref = `${base}/`;

  function childCurrent(item: NavItem): boolean {
    return item.children?.some((child) => child.current) ?? false;
  }
</script>

<div class="site-chrome">
  <header class="site-chrome__header{sectionTitle ? ' site-chrome__header--split' : ''}">
    {#if sectionTitle}
      <a class="site-chrome__brand" href={homeHref}>{siteTitle}</a>
      <a class="site-chrome__section" href={sectionHref ?? homeHref}>{sectionTitle}</a>
    {:else}
      <a class="site-chrome__brand" href={homeHref}>{siteTitle}</a>
    {/if}
  </header>

  {#if navItems.length > 0}
    <nav class="site-chrome__nav" aria-label={navLabel}>
      <ul class="site-chrome__nav-list">
        {#each navItems as item}
          <li
            class="site-chrome__nav-item"
            class:site-chrome__nav-item--has-children={item.children?.length}
            class:site-chrome__nav-item--active={item.current || childCurrent(item)}
          >
            <a
              href={item.href}
              class="site-chrome__nav-link"
              aria-current={item.current && !item.children?.length ? 'page' : undefined}
              aria-haspopup={item.children?.length ? 'menu' : undefined}
            >
              {item.label}
            </a>
            {#if item.children?.length}
              <ul class="site-chrome__nav-sub" role="menu">
                {#each item.children as child}
                  <li role="none">
                    <a href={child.href} class="site-chrome__nav-sublink" role="menuitem" aria-current={child.current ? 'page' : undefined}>
                      {child.label}
                    </a>
                  </li>
                {/each}
              </ul>
            {/if}
          </li>
        {/each}
      </ul>
    </nav>
  {/if}
</div>
