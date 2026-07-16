Piper TTS (local speech)
========================

``docker compose up`` starts a ``piper`` service on port ``5500`` exposing ``/v1/audio/speech``.

**Korean note:** upstream Piper has no official Korean neural voice that works with stock ``piper-tts``.
The Soju TTS container therefore uses **edge-tts** with ``ko-KR-SunHiNeural`` (natural Korean; needs
network). Override the voice with ``PUBLIC_TTS_PIPER_VOICE`` (e.g. ``ko-KR-InJoonNeural``). Switch engines
under **Controls → Speech** (``piper`` local service, or ``browser`` Web Speech). If the local service
is down, the app falls back to the browser.
