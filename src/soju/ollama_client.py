# SPDX-License-Identifier: BSD-3-Clause
"""Minimal Ollama HTTP client for Soju tooling."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from soju.logutil import get_logger

DEFAULT_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:31b-mlx")

logger = get_logger(__name__)


class OllamaError(RuntimeError):
    pass


def _request(
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 600,
) -> Any:
    validated = validate_base_url(base_url)
    url = f"{validated.rstrip('/')}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise OllamaError(f"Ollama HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise OllamaError(f"Cannot reach Ollama at {validated}: {exc.reason}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Ollama returned invalid JSON: {exc}") from exc


def validate_base_url(base_url: str) -> str:
    """Require an ``http`` or ``https`` base URL."""
    parsed = urllib.parse.urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OllamaError(f"Invalid Ollama base URL {base_url!r}; expected http(s)://host[:port]")
    return base_url.strip().rstrip("/")


def check_available(base_url: str = DEFAULT_BASE_URL) -> bool:
    try:
        _request(base_url, "/api/tags")
    except OllamaError:
        return False
    return True


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
    logger.debug(
        "Ollama chat request starting model=%s base_url=%s json_mode=%s payload_bytes=%s "
        "timeout_s=1200 system_chars=%s user_chars=%s",
        model,
        base_url,
        json_mode,
        payload_bytes,
        len(messages[0]["content"]) if messages else 0,
        len(messages[1]["content"]) if len(messages) > 1 else 0,
    )
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
        logger.debug("Ollama chat request failed model=%s elapsed_ms=%s error=%s", model, elapsed_ms, exc)
        raise
    elapsed_ms = int((time.monotonic() - started) * 1000)
    message = result.get("message", {})
    content = message.get("content", "")
    thinking = message.get("thinking", "")
    logger.debug(
        "Ollama chat request completed model=%s elapsed_ms=%s content_len=%s thinking_len=%s "
        "content_empty=%s message_keys=%s",
        model,
        elapsed_ms,
        len(content) if isinstance(content, str) else 0,
        len(thinking) if isinstance(thinking, str) else 0,
        not (isinstance(content, str) and content.strip()),
        list(message.keys()) if isinstance(message, dict) else [],
    )
    print(f"Ollama responded in {elapsed_ms / 1000:.0f}s.", file=sys.stderr, flush=True)
    if not isinstance(content, str) or not content.strip():
        raise OllamaError("Ollama returned an empty response.")
    return content.strip()
