# SPDX-License-Identifier: BSD-3-Clause
"""Minimal Ollama HTTP client for Soju tooling."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from soju.debug_log import debug_log

DEFAULT_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:31b-mlx")


class OllamaError(RuntimeError):
    pass


def _request(
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 600,
) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OllamaError(f"Ollama HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise OllamaError(f"Cannot reach Ollama at {base_url}: {exc.reason}") from exc


def check_available(base_url: str = DEFAULT_BASE_URL) -> bool:
    try:
        _request(base_url, "/api/tags")
        return True
    except OllamaError:
        return False


def chat(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    json_mode: bool = True,
    temperature: float = 0.3,
    num_predict: int | None = None,
) -> str:
    options: dict[str, Any] = {"temperature": temperature}
    if num_predict is not None:
        options["num_predict"] = num_predict
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    if json_mode:
        payload["format"] = "json"

    payload_bytes = len(json.dumps(payload).encode("utf-8"))
    # #region agent log
    debug_log(
        "ollama_client.py:chat:start",
        "Ollama chat request starting",
        {
            "model": model,
            "base_url": base_url,
            "json_mode": json_mode,
            "payload_bytes": payload_bytes,
            "timeout_s": 1200,
            "system_chars": len(messages[0]["content"]) if messages else 0,
            "user_chars": len(messages[1]["content"]) if len(messages) > 1 else 0,
        },
        hypothesis_id="A,C",
    )
    # #endregion
    started = time.monotonic()
    print(
        f"Calling Ollama ({model}, ~{payload_bytes // 1024} KiB request)…",
        file=sys.stderr,
        flush=True,
    )
    try:
        result = _request(base_url, "/api/chat", payload, timeout=1200)
    except OllamaError as exc:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        # #region agent log
        debug_log(
            "ollama_client.py:chat:error",
            "Ollama chat request failed",
            {"model": model, "elapsed_ms": elapsed_ms, "error": str(exc)},
            hypothesis_id="A,E",
        )
        # #endregion
        raise
    elapsed_ms = int((time.monotonic() - started) * 1000)
    message = result.get("message", {})
    content = message.get("content", "")
    thinking = message.get("thinking", "")
    # #region agent log
    debug_log(
        "ollama_client.py:chat:done",
        "Ollama chat request completed",
        {
            "model": model,
            "elapsed_ms": elapsed_ms,
            "content_len": len(content) if isinstance(content, str) else 0,
            "thinking_len": len(thinking) if isinstance(thinking, str) else 0,
            "content_empty": not (isinstance(content, str) and content.strip()),
            "message_keys": list(message.keys()) if isinstance(message, dict) else [],
        },
        hypothesis_id="B,D",
    )
    # #endregion
    print(f"Ollama responded in {elapsed_ms / 1000:.0f}s.", file=sys.stderr, flush=True)
    if not isinstance(content, str) or not content.strip():
        raise OllamaError("Ollama returned an empty response.")
    return content.strip()
