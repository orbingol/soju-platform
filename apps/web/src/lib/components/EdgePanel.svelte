<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  import { clearProgress } from '$lib/flashcards';
  import { getItem, setItem } from '$lib/storage';
  import { loadTheme, saveTheme, type ThemeMode } from '$lib/theme';
  import {
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOLUME,
    formatVoiceLabel,
    getAvailableVoices,
    getPitch,
    getRate,
    getTtsEngine,
    getVoiceUri,
    getVolume,
    hasBrowserTts,
    isTtsAvailable,
    loadTtsVoices,
    MAX_PITCH,
    MAX_RATE,
    MAX_VOLUME,
    MIN_PITCH,
    MIN_RATE,
    MIN_VOLUME,
    savePitch,
    saveRate,
    saveTtsEngine,
    saveVoiceUri,
    saveVolume,
    ttsReady,
  } from '$lib/tts';
  import type { TtsEngine } from '$lib/config';

  const PANEL_KEY = 'edge-panel-open';

  let open = $state(false);
  let theme = $state<ThemeMode>('auto');
  let ttsAvailable = $state(false);
  let engine = $state<TtsEngine>('local');
  let rate = $state(DEFAULT_RATE);
  let pitch = $state(DEFAULT_PITCH);
  let volume = $state(DEFAULT_VOLUME);
  let rateLabel = $derived(`${rate.toFixed(2)}×`);
  let pitchLabel = $derived(`${pitch.toFixed(2)}×`);
  let volumeLabel = $derived(`${Math.round(volume * 100)}%`);
  let voiceUri = $state('');
  let voiceOptions = $state<{ uri: string; label: string }[]>([]);
  let flashcardsMessage = $state('');

  async function setOpen(next: boolean) {
    open = next;
    await setItem(PANEL_KEY, next);
  }

  function toggle() {
    void setOpen(!open);
  }

  function close() {
    void setOpen(false);
  }

  async function onThemeChange(event: Event) {
    const select = event.currentTarget as HTMLSelectElement;
    theme = select.value as ThemeMode;
    await saveTheme(theme);
  }

  async function onEngineChange(event: Event) {
    const select = event.currentTarget as HTMLSelectElement;
    engine = await saveTtsEngine(select.value === 'browser' ? 'browser' : 'local');
  }

  async function onRateInput(event: Event) {
    const slider = event.currentTarget as HTMLInputElement;
    rate = await saveRate(slider.value);
  }

  async function onPitchInput(event: Event) {
    const slider = event.currentTarget as HTMLInputElement;
    pitch = await savePitch(slider.value);
  }

  async function onVolumeInput(event: Event) {
    const slider = event.currentTarget as HTMLInputElement;
    volume = await saveVolume(slider.value);
  }

  async function onVoiceChange(event: Event) {
    const select = event.currentTarget as HTMLSelectElement;
    voiceUri = select.value;
    await saveVoiceUri(voiceUri || null);
  }

  async function clearFlashcards() {
    await clearProgress();
    flashcardsMessage = 'Flashcard progress cleared.';
    window.setTimeout(() => {
      flashcardsMessage = '';
    }, 2500);
  }

  onMount(() => {
    if (!browser) return;

    void (async () => {
      const storedOpen = await getItem<boolean>(PANEL_KEY);
      open = storedOpen === true;
      theme = await loadTheme();
      await ttsReady();
      ttsAvailable = isTtsAvailable();
      engine = getTtsEngine();
      rate = getRate();
      pitch = getPitch();
      volume = getVolume();
      voiceUri = getVoiceUri() ?? '';

      if (hasBrowserTts) {
        await loadTtsVoices();
        voiceOptions = getAvailableVoices().map((entry) => ({
          uri: entry.voiceURI,
          label: formatVoiceLabel(entry),
        }));

        if (voiceUri && !voiceOptions.some((entry) => entry.uri === voiceUri)) {
          voiceUri = '';
          await saveVoiceUri(null);
        }
      }
    })();

    const onKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) {
        close();
      }
    };

    document.addEventListener('keydown', onKeydown);
    return () => document.removeEventListener('keydown', onKeydown);
  });
</script>

<aside class="edge-panel" id="edge-panel" class:is-open={open} aria-label="Settings panel">
  <div class="edge-panel__header">
    <h2>Controls</h2>
    <button type="button" class="outline secondary" data-edge-close aria-label="Close settings panel" onclick={close}> Close </button>
  </div>

  <section class="edge-panel__section">
    <h3>Appearance</h3>
    <div class="setting-row">
      <label for="setting-theme">Theme</label>
      <select id="setting-theme" name="theme" value={theme} onchange={onThemeChange}>
        <option value="auto">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  </section>

  {#if ttsAvailable}
    <section class="edge-panel__section" id="tts-settings">
      <h3>Speech</h3>
      <div class="setting-row">
        <label for="tts-engine">Engine</label>
        <select id="tts-engine" name="tts-engine" value={engine} onchange={onEngineChange}>
          <option value="local">Local TTS</option>
          <option value="browser" disabled={!hasBrowserTts}>Browser</option>
        </select>
      </div>
      {#if engine === 'browser' && voiceOptions.length > 0}
        <div class="setting-row">
          <label for="tts-voice">Voice</label>
          <select id="tts-voice" name="tts-voice" value={voiceUri} onchange={onVoiceChange}>
            <option value="">System default</option>
            {#each voiceOptions as option (option.uri)}
              <option value={option.uri}>{option.label}</option>
            {/each}
          </select>
        </div>
      {/if}
      <div class="setting-row">
        <div class="setting-label-row">
          <label for="tts-rate">Speed</label>
          <output class="setting-value" id="tts-rate-value" for="tts-rate">{rateLabel}</output>
        </div>
        <input type="range" id="tts-rate" name="tts-rate" min={MIN_RATE} max={MAX_RATE} step="0.05" value={rate} oninput={onRateInput} />
      </div>
      {#if engine === 'browser'}
        <div class="setting-row">
          <div class="setting-label-row">
            <label for="tts-pitch">Pitch</label>
            <output class="setting-value" id="tts-pitch-value" for="tts-pitch">{pitchLabel}</output>
          </div>
          <input type="range" id="tts-pitch" name="tts-pitch" min={MIN_PITCH} max={MAX_PITCH} step="0.05" value={pitch} oninput={onPitchInput} />
        </div>
      {/if}
      <div class="setting-row">
        <div class="setting-label-row">
          <label for="tts-volume">Volume</label>
          <output class="setting-value" id="tts-volume-value" for="tts-volume">{volumeLabel}</output>
        </div>
        <input type="range" id="tts-volume" name="tts-volume" min={MIN_VOLUME} max={MAX_VOLUME} step="0.05" value={volume} oninput={onVolumeInput} />
      </div>
      {#if engine === 'local'}
        <p class="setting-note">Local TTS uses the Soju backend neural Korean voice (edge-tts; needs network). Falls back to browser speech if the service is offline.</p>
      {/if}
    </section>
  {/if}

  <section class="edge-panel__section">
    <h3>Flashcards</h3>
    <div class="setting-row">
      <p class="setting-note">Clears known/unknown marks and deck position.</p>
      <button type="button" class="outline secondary" onclick={clearFlashcards}>Clear progress</button>
      {#if flashcardsMessage}
        <p class="setting-feedback" role="status">{flashcardsMessage}</p>
      {/if}
    </div>
  </section>
</aside>

<button
  type="button"
  class="edge-handle"
  id="edge-handle"
  aria-controls="edge-panel"
  aria-expanded={open}
  aria-label={open ? 'Close settings panel' : 'Open settings panel'}
  onclick={toggle}
></button>

<div class="edge-backdrop" id="edge-backdrop" class:is-visible={open} hidden={!open} role="presentation" onclick={close}></div>
