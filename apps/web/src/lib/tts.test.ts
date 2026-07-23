import { describe, expect, it } from 'vitest';

import { aiEmbedModel, aiModel, applyClientConfig, localTtsVoice, resolveTtsEngine } from './config';
import { formatVoiceLabel, getTtsEngine, isKoreanVoice, pickVoices, resolveVoiceByUri, setPitch, setRate, setTtsEngine, setVoiceUri, setVolume } from './tts';

function voice(name: string, lang: string, uri = name): SpeechSynthesisVoice {
  return { name, lang, voiceURI: uri } as SpeechSynthesisVoice;
}

describe('tts', () => {
  it('detects Korean voices by language tag', () => {
    expect(isKoreanVoice(voice('Yuna', 'ko-KR'))).toBe(true);
    expect(isKoreanVoice(voice('English', 'en-US'))).toBe(false);
  });

  it('prefers Korean voices but falls back to all voices', () => {
    const mixed = [voice('English', 'en-US'), voice('Yuna', 'ko-KR'), voice('Anna', 'en-GB')];

    expect(pickVoices(mixed).map((entry) => entry.name)).toEqual(['Yuna']);

    const englishOnly = [voice('English', 'en-US'), voice('Anna', 'en-GB')];
    expect(pickVoices(englishOnly).map((entry) => entry.name)).toEqual(['Anna', 'English']);
  });

  it('formats voice labels with language', () => {
    expect(formatVoiceLabel(voice('Yuna', 'ko-KR'))).toBe('Yuna (ko-KR)');
  });

  it('resolves a stored voice URI', () => {
    const voices = [voice('Yuna', 'ko-KR', 'ko-yuna'), voice('English', 'en-US', 'en-us')];
    expect(resolveVoiceByUri(voices, 'ko-yuna')?.name).toBe('Yuna');
    expect(resolveVoiceByUri(voices, 'missing')).toBeNull();
    expect(resolveVoiceByUri(voices, null)).toBeNull();
  });

  it('normalizes empty voice URIs', () => {
    expect(setVoiceUri(' ko-yuna ')).toBe('ko-yuna');
    expect(setVoiceUri('')).toBeNull();
    expect(setVoiceUri(undefined)).toBeNull();
  });

  it('clamps rate, pitch, and volume', () => {
    expect(setRate(2)).toBe(1.5);
    expect(setRate(0.1)).toBe(0.25);
    expect(setPitch(2)).toBe(1.5);
    expect(setPitch(0.1)).toBe(0.25);
    expect(setVolume(1.5)).toBe(1);
    expect(setVolume(-0.5)).toBe(0);
  });

  it('resolves and stores TTS engine selection', () => {
    expect(resolveTtsEngine('browser')).toBe('browser');
    expect(resolveTtsEngine('PIPER')).toBe('local');
    expect(resolveTtsEngine('local')).toBe('local');
    expect(resolveTtsEngine(undefined)).toBe('local');
    expect(setTtsEngine('browser')).toBe('browser');
    expect(getTtsEngine()).toBe('browser');
    expect(setTtsEngine('local')).toBe('local');
    expect(getTtsEngine()).toBe('local');
  });

  it('applies client-config model overrides', () => {
    applyClientConfig({ chat_model: 'test-chat', embed_model: 'test-embed', tts_default_voice: 'ko-KR-InJoonNeural' });
    expect(aiModel).toBe('test-chat');
    expect(aiEmbedModel).toBe('test-embed');
    expect(localTtsVoice).toBe('ko-KR-InJoonNeural');
  });
});
