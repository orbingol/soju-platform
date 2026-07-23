<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { browser } from '$app/environment';

  import { checkAiAvailable } from '$lib/ai/client';
  import { ensureClientConfig } from '$lib/ai/client-config';
  import { buildChatSystemPrompt, chatTutorLabel, GLOBAL_CHAT_SESSION_KEY, loadChatDockOpen, saveChatDockOpen } from '$lib/chat';
  import { openChatPopoutWindow } from '$lib/chat-popout';
  import { aiBaseUrl, aiModel, aiTutorName } from '$lib/config';

  import ChatConversation from '$lib/components/ChatConversation.svelte';

  interface ChatConfig {
    model: string;
    systemPrompt: string;
    tutorName: string;
    tutorLabel: string;
  }

  interface Props {
    chat: ChatConfig;
  }

  let { chat }: Props = $props();

  let open = $state(false);
  let checking = $state(true);
  let available = $state(false);
  let poppedOut = $state(false);
  let conversation: ChatConversation | undefined = $state();
  let panelHost: HTMLDivElement | undefined = $state();
  let panelEl: HTMLElement | undefined = $state();
  let popoutWindow: Window | null = null;
  let removePopoutListeners: (() => void) | null = null;

  let model = $state(chat.model);
  let systemPrompt = $state(chat.systemPrompt);
  let tutorName = $state(chat.tutorName);
  let tutorLabel = $state(chat.tutorLabel);

  const tutorShortName = $derived(tutorName.split('(')[0]?.trim() || tutorName);
  const tutorInitial = $derived([...tutorShortName][0] ?? '희');

  async function setOpen(next: boolean) {
    open = next;
    await saveChatDockOpen(next);
  }

  function toggle() {
    if (poppedOut) {
      void popIn();
      return;
    }
    void setOpen(!open);
  }

  function close() {
    if (poppedOut) {
      void popIn().then(() => setOpen(false));
      return;
    }
    void setOpen(false);
  }

  function refresh() {
    void conversation?.refreshConversation();
  }

  function restorePanel() {
    if (!panelHost || !panelEl) return;
    if (panelEl.parentElement !== panelHost) {
      panelHost.appendChild(panelEl);
    }
  }

  function clearPopoutListeners() {
    removePopoutListeners?.();
    removePopoutListeners = null;
  }

  /**
   * Svelte 5 delegates events to the app document, so once the panel lives in a
   * PiP/popup window those handlers never fire. Bind native listeners instead.
   */
  function bindPopoutListeners() {
    clearPopoutListeners();
    if (!panelEl) return;

    const pairs: Array<[string, (event: Event) => void]> = [
      [
        'popout',
        (event) => {
          event.preventDefault();
          event.stopPropagation();
          void popIn();
        },
      ],
      [
        'refresh',
        (event) => {
          event.preventDefault();
          event.stopPropagation();
          refresh();
        },
      ],
      [
        'close',
        (event) => {
          event.preventDefault();
          event.stopPropagation();
          close();
        },
      ],
    ];

    const cleanups: Array<() => void> = [];
    for (const [action, handler] of pairs) {
      const button = panelEl.querySelector(`[data-chat-action="${action}"]`);
      if (!button) continue;
      button.addEventListener('click', handler);
      cleanups.push(() => button.removeEventListener('click', handler));
    }

    removePopoutListeners = () => {
      for (const cleanup of cleanups) cleanup();
    };
  }

  async function popIn() {
    const win = popoutWindow;
    clearPopoutListeners();
    restorePanel();
    popoutWindow = null;
    poppedOut = false;

    if (win && !win.closed) {
      try {
        win.close();
      } catch {
        // Document PiP may already be closing after the node moved back.
      }
    }

    await setOpen(true);
  }

  async function popOut() {
    if (poppedOut || !panelEl) return;

    await setOpen(true);

    const win = await openChatPopoutWindow({
      width: 400,
      height: 560,
      title: chat.tutorLabel,
    });
    if (!win) return;

    popoutWindow = win;
    win.document.body.appendChild(panelEl);
    poppedOut = true;
    bindPopoutListeners();

    const onWindowGone = () => {
      if (!poppedOut) return;
      clearPopoutListeners();
      restorePanel();
      popoutWindow = null;
      poppedOut = false;
      void setOpen(true);
    };

    win.addEventListener('pagehide', onWindowGone);
    win.addEventListener('unload', onWindowGone);
  }

  async function togglePopout() {
    if (poppedOut) {
      await popIn();
    } else {
      await popOut();
    }
  }

  onMount(() => {
    if (!browser) return;

    void (async () => {
      await ensureClientConfig();
      model = aiModel;
      systemPrompt = buildChatSystemPrompt();
      tutorName = aiTutorName;
      tutorLabel = chatTutorLabel(aiTutorName);
      open = await loadChatDockOpen();
      available = await checkAiAvailable();
      checking = false;
    })();

    const onOpenRequest = () => {
      void setOpen(true);
    };

    const onKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open && !poppedOut) {
        close();
      }
    };

    window.addEventListener('soju:chat-open', onOpenRequest);
    document.addEventListener('keydown', onKeydown);

    return () => {
      window.removeEventListener('soju:chat-open', onOpenRequest);
      document.removeEventListener('keydown', onKeydown);
    };
  });

  onDestroy(() => {
    clearPopoutListeners();
    if (popoutWindow && !popoutWindow.closed) {
      try {
        popoutWindow.close();
      } catch {
        // ignore
      }
    }
  });

  const ready = $derived(!checking && available);
  const offline = $derived(!checking && !available);
</script>

<div class="chat-dock" class:is-open={open} class:is-popped-out={poppedOut}>
  <div class="chat-dock__panel-host" bind:this={panelHost}>
    <aside class="chat-dock__panel" id="chat-dock-panel" bind:this={panelEl} aria-label={tutorLabel}>
      <div class="chat-dock__header">
        <div class="chat-dock__identity">
          <span class="chat-dock__avatar" aria-hidden="true">{tutorInitial}</span>
          <div class="chat-dock__titles">
            <h2>{tutorShortName}</h2>
            <p class="chat-dock__subtitle">Korean tutor</p>
          </div>
        </div>
        <div class="chat-dock__actions">
          <button
            type="button"
            class="chat-dock__icon-btn"
            data-chat-action="popout"
            aria-label={poppedOut ? 'Pop chat back into the page' : 'Pop chat out into a floating window'}
            title={poppedOut ? 'Pop in' : 'Pop out'}
            onclick={() => void togglePopout()}
            disabled={!ready && !poppedOut}
          >
            {poppedOut ? 'Pop in' : 'Pop out'}
          </button>
          <button type="button" class="chat-dock__icon-btn" data-chat-action="refresh" aria-label="Start a new conversation" title="Refresh" onclick={refresh} disabled={!ready}>
            Refresh
          </button>
          <button type="button" class="chat-dock__icon-btn chat-dock__icon-btn--close" data-chat-action="close" aria-label="Close chat" title="Close" onclick={close}>
            Close
          </button>
        </div>
      </div>

      <div class="chat-dock__body">
        {#if checking}
          <p class="ai-status" role="status">Checking language model service…</p>
        {:else if offline}
          <p class="ai-status ai-status--offline" role="status">
            Chat is unavailable at <code>{aiBaseUrl}</code>. Confirm the model service is running, CORS allows
            <code>{typeof window !== 'undefined' ? window.location.origin : 'this site'}</code>, then reload.
          </p>
        {:else}
          <ChatConversation bind:this={conversation} systemPrompt={systemPrompt} model={model} sessionKey={GLOBAL_CHAT_SESSION_KEY} compact />
        {/if}
      </div>
    </aside>
  </div>

  <button
    type="button"
    class="chat-dock__handle"
    class:chat-dock__handle--return={poppedOut}
    aria-controls="chat-dock-panel"
    aria-expanded={open && !poppedOut}
    aria-label={poppedOut ? `Pop ${chat.tutorLabel} back into the page` : open ? `Close ${chat.tutorLabel}` : chat.tutorLabel}
    onclick={toggle}
  >
    {poppedOut ? `Pop in · ${tutorShortName}` : chat.tutorLabel}
  </button>
</div>

<div class="chat-dock-backdrop" class:is-visible={open && !poppedOut} hidden={!open || poppedOut} role="presentation" onclick={close}></div>
