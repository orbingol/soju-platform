Local TTS (speech)
==================

``docker compose up`` starts the Soju ``backend`` (behind nginx on port ``8080``).
Speak buttons call ``POST /v1/audio/speech`` on that API.

**Korean note:** upstream Piper has no official Korean neural voice that works with stock
``piper-tts``. The backend defaults to **edge-tts** (``tts.engine: edge``) with
``ko-KR-SunHiNeural``. Override voice / engine in backend YAML
(``~/.config/soju/backend.yaml`` or ``config/backend.yaml``). Native Piper is available
when you set ``tts.engine: piper`` and a valid ``tts.piper.model_path``.

In the UI, choose **Controls → Speech**: ``local`` (Soju backend) or ``browser``
(Web Speech). If local TTS is down, the app falls back to the browser.

Default browser env: ``PUBLIC_TTS_ENGINE=local`` and ``PUBLIC_AI_BASE_URL=http://localhost:8080``
(same origin as the API).
