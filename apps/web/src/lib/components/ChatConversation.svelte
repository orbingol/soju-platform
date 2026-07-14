<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  import { complete, streamCompletion } from '$lib/ai/client';
  import { clearConversationId } from '$lib/ai/conversation-store';
  import { buildModelMessages, clearChatMemory, ensureChatMemory, loadChatMemory, needsSummarization, type ChatMemory } from '$lib/chat-context';
  import { type ChatTurn, loadChatMessages, saveChatMessages } from '$lib/chat';
  import { formatChatContent } from '$lib/format-chat-content';

  type ReplyPhase = 'idle' | 'summarizing' | 'thinking' | 'streaming';

  interface Props {
    systemPrompt: string;
    model: string;
    sessionKey: string;
    disabled?: boolean;
    compact?: boolean;
  }

  let { systemPrompt, model, sessionKey, disabled = false, compact = false }: Props = $props();

  let input = $state('');
  let sending = $state(false);
  let error = $state('');
  let messages = $state<ChatTurn[]>([]);
  let hydrated = $state(false);
  let replyPhase = $state<ReplyPhase>('idle');
  let memory = $state<ChatMemory | null>(null);
  let logEl: HTMLDivElement | undefined = $state();

  async function persistMessages(next: ChatTurn[]) {
    messages = next;
    if (hydrated) {
      await saveChatMessages(next);
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || sending || disabled) return;

    input = '';
    sending = true;
    error = '';
    replyPhase = 'thinking';

    const nextMessages: ChatTurn[] = [...messages, { role: 'user', content: text }];
    await persistMessages([...nextMessages, { role: 'assistant', content: '' }]);

    try {
      if (needsSummarization(nextMessages.length, memory)) {
        replyPhase = 'summarizing';
        const result = await ensureChatMemory({
          messages: nextMessages,
          model,
          memory,
          complete,
        });
        memory = result.memory;
      }

      replyPhase = 'thinking';
      const history = buildModelMessages(systemPrompt, nextMessages, memory);

      for await (const token of streamCompletion({
        messages: history,
        model,
        sessionKey,
      })) {
        if (replyPhase !== 'streaming') {
          replyPhase = 'streaming';
        }
        messages = messages.map((message, index) => (index === messages.length - 1 ? { ...message, content: message.content + token } : message));
        logEl?.scrollTo({ top: logEl.scrollHeight, behavior: 'smooth' });
      }
      await saveChatMessages(messages);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Chat failed';
      await persistMessages(messages.slice(0, -1));
    } finally {
      sending = false;
      replyPhase = 'idle';
    }
  }

  /** Native submit — survives moving the panel into a PiP/popup window. */
  function nativeSubmit(node: HTMLFormElement) {
    const onFormSubmit = (event: Event) => {
      event.preventDefault();
      void send();
    };
    node.addEventListener('submit', onFormSubmit);
    return {
      destroy() {
        node.removeEventListener('submit', onFormSubmit);
      },
    };
  }

  export async function refreshConversation() {
    error = '';
    input = '';
    messages = [];
    memory = null;
    replyPhase = 'idle';
    hydrated = true;
    await saveChatMessages([]);
    await clearChatMemory();
    await clearConversationId(sessionKey);
  }

  onMount(() => {
    if (!browser) return;

    void (async () => {
      messages = await loadChatMessages();
      memory = await loadChatMemory();
      hydrated = true;
    })();
  });

  function pendingLabel(phase: ReplyPhase): string {
    if (phase === 'summarizing') return 'Summarizing…';
    return 'Thinking…';
  }
</script>

<div class="chat-conversation" class:chat-conversation--compact={compact}>
  <div class="chat-log chat-log--{compact ? 'compact' : 'full'}" bind:this={logEl}>
    {#if messages.length === 0}
      <p class="practice-status">Ask a question to start the lesson.</p>
    {/if}
    {#each messages as message, index (index)}
      {#if message.role === 'assistant'}
        <div class="chat-bubble chat-bubble--assistant" class:chat-bubble--pending={!message.content} aria-busy={!message.content && sending}>
          {#if !message.content}
            <p class="chat-bubble__pending"><em>{pendingLabel(replyPhase)}</em></p>
          {:else}
            {@html formatChatContent(message.content)}
          {/if}
        </div>
      {:else}
        <div class="chat-bubble chat-bubble--user">{message.content}</div>
      {/if}
    {/each}
  </div>

  {#if error}
    <p class="chat-conversation__error" role="alert">{error}</p>
  {/if}

  <form class="chat-form" class:chat-form--compact={compact} use:nativeSubmit>
    {#if compact}
      <input type="text" bind:value={input} placeholder="Ask in English or Korean…" disabled={sending || disabled} />
    {:else}
      <textarea bind:value={input} placeholder="Ask in English or Korean…" disabled={sending || disabled} rows={3}></textarea>
    {/if}
    <button type="submit" class="chat-form__send" disabled={sending || disabled || !input.trim()}>{sending ? '…' : 'Send'}</button>
  </form>
</div>
