Local TTS (speech)
==================

``uv run poe up`` serves the API (including ``POST /v1/audio/speech``) on ``:14322``.
``poe up-prod`` / ``docker compose up`` serve speech at ``POST /api/v1/audio/speech`` through nginx.

**Korean note:** upstream Piper has no official Korean neural voice that works with stock
``piper-tts``. The backend defaults to **edge-tts** (``tts.engine: edge``) with
``ko-KR-SunHiNeural``. Override voice / engine in backend YAML
(``~/.config/soju/backend.yaml`` or ``docker/soju/backend.yaml``). Native Piper is available
when you set ``tts.engine: piper`` and a valid ``tts.piper.model_path``.

In the UI, choose **Controls → Speech**: ``local`` (Soju backend) or ``browser``
(Web Speech). If local TTS is down, the app falls back to the browser.

Default browser env: ``PUBLIC_TTS_ENGINE=local`` and
``PUBLIC_AI_BASE_URL=http://localhost:14322`` (dev) or ``/api`` (prod).
