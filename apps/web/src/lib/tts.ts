import { defaultTtsEngine, localTtsBaseUrl, localTtsVoice, type TtsEngine } from '$lib/config';
import { getItem, setItem } from '$lib/storage';

const TTS_RATE_KEY = 'tts-rate';
const TTS_PITCH_KEY = 'tts-pitch';
const TTS_VOLUME_KEY = 'tts-volume';
const TTS_VOICE_KEY = 'tts-voice-uri';
const TTS_ENGINE_KEY = 'tts-engine';

export const MIN_RATE = 0.25;
export const MAX_RATE = 1.5;
export const DEFAULT_RATE = 0.5;

export const MIN_PITCH = 0.25;
export const MAX_PITCH = 1.5;
export const DEFAULT_PITCH = 1;

export const MIN_VOLUME = 0;
export const MAX_VOLUME = 1;
export const DEFAULT_VOLUME = 1;

/** True when the browser Web Speech API is available. */
export const hasBrowserTts = typeof window !== 'undefined' && !!window.speechSynthesis;

let activeBtn: HTMLButtonElement | null = null;
let activeAudio: HTMLAudioElement | null = null;
let activeObjectUrl: string | null = null;
let rate = DEFAULT_RATE;
let pitch = DEFAULT_PITCH;
let volume = DEFAULT_VOLUME;
let selectedVoiceUri: string | null = null;
let selectedEngine: TtsEngine = defaultTtsEngine;
let readyPromise: Promise<void> | null = null;

export function isKoreanVoice(voice: SpeechSynthesisVoice): boolean {
  return voice.lang.toLowerCase().startsWith('ko');
}

export function formatVoiceLabel(voice: SpeechSynthesisVoice): string {
  return `${voice.name} (${voice.lang})`;
}

export function pickVoices(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  const korean = voices.filter(isKoreanVoice);
  const list = korean.length > 0 ? korean : voices;
  return [...list].sort((a, b) => a.name.localeCompare(b.name));
}

export function resolveVoiceByUri(voices: SpeechSynthesisVoice[], uri: string | null | undefined): SpeechSynthesisVoice | null {
  if (!uri) return null;
  return voices.find((voice) => voice.voiceURI === uri) ?? null;
}

function clampRate(value: number | string): number {
  const parsed = Number.parseFloat(String(value));
  if (Number.isNaN(parsed)) return DEFAULT_RATE;
  return Math.min(MAX_RATE, Math.max(MIN_RATE, parsed));
}

function clampPitch(value: number | string): number {
  const parsed = Number.parseFloat(String(value));
  if (Number.isNaN(parsed)) return DEFAULT_PITCH;
  return Math.min(MAX_PITCH, Math.max(MIN_PITCH, parsed));
}

function clampVolume(value: number | string): number {
  const parsed = Number.parseFloat(String(value));
  if (Number.isNaN(parsed)) return DEFAULT_VOLUME;
  return Math.min(MAX_VOLUME, Math.max(MIN_VOLUME, parsed));
}

export function setRate(value: number | string): number {
  rate = clampRate(value);
  return rate;
}

export function getRate(): number {
  return rate;
}

export function setPitch(value: number | string): number {
  pitch = clampPitch(value);
  return pitch;
}

export function getPitch(): number {
  return pitch;
}

export function setVolume(value: number | string): number {
  volume = clampVolume(value);
  return volume;
}

export function getVolume(): number {
  return volume;
}

export function setVoiceUri(uri: string | null | undefined): string | null {
  const trimmed = uri?.trim();
  selectedVoiceUri = trimmed ? trimmed : null;
  return selectedVoiceUri;
}

export function getVoiceUri(): string | null {
  return selectedVoiceUri;
}

export function setTtsEngine(engine: TtsEngine): TtsEngine {
  selectedEngine = engine === 'browser' ? 'browser' : 'local';
  return selectedEngine;
}

export function getTtsEngine(): TtsEngine {
  return selectedEngine;
}

/** Speech is usable via local Soju TTS and/or browser voices. */
export function isTtsAvailable(): boolean {
  return selectedEngine === 'local' || hasBrowserTts;
}

function getBrowserVoices(): SpeechSynthesisVoice[] {
  if (!hasBrowserTts) return [];
  return window.speechSynthesis.getVoices();
}

export function getAvailableVoices(): SpeechSynthesisVoice[] {
  return pickVoices(getBrowserVoices());
}

function getSelectedVoice(): SpeechSynthesisVoice | null {
  return resolveVoiceByUri(getBrowserVoices(), selectedVoiceUri);
}

function waitForVoices(timeoutMs = 1000): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    if (!hasBrowserTts) {
      resolve([]);
      return;
    }

    const finish = () => resolve(getAvailableVoices());

    const loaded = getAvailableVoices();
    if (loaded.length > 0) {
      finish();
      return;
    }

    let settled = false;
    const settle = () => {
      if (settled) return;
      settled = true;
      window.speechSynthesis.removeEventListener('voiceschanged', settle);
      finish();
    };

    window.speechSynthesis.addEventListener('voiceschanged', settle);
    window.speechSynthesis.getVoices();
    window.setTimeout(settle, timeoutMs);
  });
}

async function loadStoredRate(): Promise<void> {
  try {
    const legacy = localStorage.getItem('kr-edu-tts-rate');
    if (legacy !== null) {
      rate = clampRate(legacy);
      await setItem(TTS_RATE_KEY, rate);
      localStorage.removeItem('kr-edu-tts-rate');
      return;
    }
  } catch {
    // Ignore migration errors.
  }

  const stored = await getItem<number>(TTS_RATE_KEY);
  if (stored !== null) {
    rate = clampRate(stored);
  }
}

async function loadStoredPitch(): Promise<void> {
  const stored = await getItem<number>(TTS_PITCH_KEY);
  if (stored !== null) {
    pitch = clampPitch(stored);
  }
}

async function loadStoredVolume(): Promise<void> {
  const stored = await getItem<number>(TTS_VOLUME_KEY);
  if (stored !== null) {
    volume = clampVolume(stored);
  }
}

async function loadStoredVoice(): Promise<void> {
  const stored = await getItem<string>(TTS_VOICE_KEY);
  if (typeof stored === 'string' && stored.trim()) {
    selectedVoiceUri = stored;
  }
}

async function loadStoredEngine(): Promise<void> {
  const stored = await getItem<string>(TTS_ENGINE_KEY);
  if (stored === 'browser') {
    selectedEngine = 'browser';
    return;
  }
  if (stored === 'local' || stored === 'piper') {
    selectedEngine = 'local';
    if (stored === 'piper') {
      await setItem(TTS_ENGINE_KEY, 'local');
    }
    return;
  }
  selectedEngine = defaultTtsEngine;
}

async function loadStoredSettings(): Promise<void> {
  await Promise.all([loadStoredRate(), loadStoredPitch(), loadStoredVolume(), loadStoredVoice(), loadStoredEngine()]);
}

export function ttsReady(): Promise<void> {
  if (!readyPromise) {
    readyPromise = loadStoredSettings();
  }
  return readyPromise;
}

export function loadTtsVoices(): Promise<SpeechSynthesisVoice[]> {
  return waitForVoices();
}

export async function saveVoiceUri(uri: string | null | undefined): Promise<string | null> {
  const next = setVoiceUri(uri);
  if (next) {
    await setItem(TTS_VOICE_KEY, next);
  } else {
    await setItem(TTS_VOICE_KEY, null);
  }
  return next;
}

export async function saveRate(value: number | string): Promise<number> {
  const next = setRate(value);
  await setItem(TTS_RATE_KEY, next);
  return next;
}

export async function savePitch(value: number | string): Promise<number> {
  const next = setPitch(value);
  await setItem(TTS_PITCH_KEY, next);
  return next;
}

export async function saveVolume(value: number | string): Promise<number> {
  const next = setVolume(value);
  await setItem(TTS_VOLUME_KEY, next);
  return next;
}

export async function saveTtsEngine(engine: TtsEngine): Promise<TtsEngine> {
  const next = setTtsEngine(engine);
  await setItem(TTS_ENGINE_KEY, next);
  return next;
}

export async function checkLocalTtsAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${localTtsBaseUrl}/health`, { method: 'GET' });
    if (!response.ok) return false;
    const payload = (await response.json()) as { ok?: boolean };
    return payload.ok === true;
  } catch {
    return false;
  }
}

/** @deprecated Use {@link checkLocalTtsAvailable}. */
export const checkPiperAvailable = checkLocalTtsAvailable;

function clearSpeakingUi(): void {
  if (activeBtn) {
    activeBtn.classList.remove('speaking');
  }
  activeBtn = null;
}

function stopPlayback(): void {
  if (hasBrowserTts) {
    window.speechSynthesis.cancel();
  }
  if (activeAudio) {
    activeAudio.pause();
    activeAudio = null;
  }
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl);
    activeObjectUrl = null;
  }
  clearSpeakingUi();
}

function speakWithBrowser(text: string, btn?: HTMLButtonElement | null): void {
  if (!hasBrowserTts || !text) return;

  stopPlayback();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'ko-KR';
  utterance.rate = getRate();
  utterance.pitch = getPitch();
  utterance.volume = getVolume();

  const voice = getSelectedVoice();
  if (voice) {
    utterance.voice = voice;
  }

  activeBtn = btn ?? null;
  if (activeBtn) {
    activeBtn.classList.add('speaking');
  }

  utterance.onend = clearSpeakingUi;
  utterance.onerror = clearSpeakingUi;

  window.speechSynthesis.speak(utterance);
}

async function speakWithLocalTts(text: string, btn?: HTMLButtonElement | null): Promise<void> {
  stopPlayback();

  activeBtn = btn ?? null;
  if (activeBtn) {
    activeBtn.classList.add('speaking');
  }

  const response = await fetch(`${localTtsBaseUrl}/v1/audio/speech`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: localTtsVoice,
      voice: localTtsVoice,
      input: text,
      speed: getRate(),
    }),
  });

  if (!response.ok) {
    throw new Error(`Local TTS failed (${response.status})`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  activeObjectUrl = objectUrl;

  const audio = new Audio(objectUrl);
  audio.volume = getVolume();
  activeAudio = audio;

  const finish = () => {
    if (activeAudio === audio) {
      activeAudio = null;
    }
    if (activeObjectUrl === objectUrl) {
      URL.revokeObjectURL(objectUrl);
      activeObjectUrl = null;
    }
    clearSpeakingUi();
  };

  audio.addEventListener('ended', finish);
  audio.addEventListener('error', finish);
  await audio.play();
}

/**
 * Speak Hangul (or other text). Uses local Soju TTS when selected, falling back to
 * browser Web Speech if the service is unavailable.
 */
export function speak(text: string, btn?: HTMLButtonElement | null): void {
  if (!text.trim()) return;
  void (async () => {
    await ttsReady();
    if (getTtsEngine() === 'local') {
      try {
        await speakWithLocalTts(text, btn);
        return;
      } catch {
        // Fall through to browser when local TTS is down.
      }
    }
    speakWithBrowser(text, btn);
  })();
}

export function bindSpeakButtons(root: ParentNode): void {
  if (!isTtsAvailable()) return;

  root.querySelectorAll<HTMLButtonElement>('.spk[data-text]').forEach((btn) => {
    if (btn.dataset.ttsBound === 'true') return;
    btn.dataset.ttsBound = 'true';

    btn.addEventListener('click', (event) => {
      event.stopPropagation();
      speak(btn.dataset.text ?? '', btn);
    });
  });
}

export function showNoTtsBanner(root: ParentNode = document): void {
  const banner = root.querySelector<HTMLElement>('.verb-no-tts');
  if (!banner) return;

  if (isTtsAvailable()) {
    banner.hidden = true;
    return;
  }

  banner.hidden = false;
  root.querySelectorAll('[data-verb-table], [data-word-table]').forEach((table) => {
    table.classList.add('no-tts');
  });
}
