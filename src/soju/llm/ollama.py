# SPDX-License-Identifier: BSD-3-Clause
"""Ollama HTTP client implementing :class:`~soju.llm.base.LlmClient`."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from soju.core.logging import get_logger
from soju.llm.base import ChatMessage, LlmError

DEFAULT_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")

logger = get_logger(__name__)


class OllamaError(LlmError):
    """Raised when an Ollama request fails or returns an invalid response."""


def validate_base_url(base_url: str) -> str:
    """Require an ``http`` or ``https`` base URL.

    Args:
        base_url: Candidate Ollama base URL.

    Returns:
        Stripped URL without a trailing slash.

    Raises:
        OllamaError: If the URL is not http(s) with a host.
    """
    parsed = urllib.parse.urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OllamaError(f"Invalid Ollama base URL {base_url!r}; expected http(s)://host[:port]")
    return base_url.strip().rstrip("/")


def _request(
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 600,
) -> Any:
    """Perform a GET/POST against an Ollama HTTP API path."""
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


class OllamaClient:
    """Concrete :class:`~soju.llm.base.LlmClient` backed by Ollama's HTTP API."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Create a client bound to ``model`` and ``base_url``.

        Args:
            model: Default Ollama model name.
            base_url: Default Ollama base URL.
        """
        self.model = model
        self.base_url = base_url

    def check_available(self) -> bool:
        """Return True when the Ollama tags endpoint responds successfully."""
        try:
            _request(self.base_url, "/api/tags")
        except OllamaError:
            return False
        return True

    def chat(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        json_mode: bool = True,
        temperature: float = 0.3,
        num_predict: int | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> str:
        """Send a chat request and return the assistant content.

        Args:
            messages: Chat messages (typically system + user).
            json_mode: When True, request JSON-formatted output.
            temperature: Sampling temperature.
            num_predict: Optional max tokens / predict length.
            model: Optional per-call model override.
            base_url: Optional per-call base URL override.

        Returns:
            Non-empty assistant content string.

        Raises:
            OllamaError: On transport failures or empty responses.
        """
        use_model = model if model is not None else self.model
        use_base = base_url if base_url is not None else self.base_url
        options: dict[str, Any] = {"temperature": temperature}
        if num_predict is not None:
            options["num_predict"] = num_predict
        payload: dict[str, Any] = {
            "model": use_model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if json_mode:
            payload["format"] = "json"

        payload_bytes = len(json.dumps(payload).encode("utf-8"))
        logger.debug(
            "Ollama chat request starting model=%s base_url=%s json_mode=%s payload_bytes=%s timeout_s=1200 system_chars=%s user_chars=%s",
            use_model,
            use_base,
            json_mode,
            payload_bytes,
            len(messages[0]["content"]) if messages else 0,
            len(messages[1]["content"]) if len(messages) > 1 else 0,
        )
        started = time.monotonic()
        print(
            f"Calling Ollama ({use_model}, ~{payload_bytes // 1024} KiB request)…",
            file=sys.stderr,
            flush=True,
        )
        try:
            result = _request(use_base, "/api/chat", payload, timeout=1200)
        except OllamaError as exc:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            logger.debug("Ollama chat request failed model=%s elapsed_ms=%s error=%s", use_model, elapsed_ms, exc)
            raise
        elapsed_ms = int((time.monotonic() - started) * 1000)
        message = result.get("message", {})
        content = message.get("content", "")
        thinking = message.get("thinking", "")
        logger.debug(
            "Ollama chat request completed model=%s elapsed_ms=%s content_len=%s thinking_len=%s content_empty=%s message_keys=%s",
            use_model,
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

    def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        base_url: str | None = None,
    ) -> list[float]:
        """Return an embedding vector for ``text`` via ``/api/embeddings``.

        Args:
            text: Text to embed.
            model: Optional per-call embedding model override.
            base_url: Optional per-call base URL override.

        Returns:
            The embedding vector.

        Raises:
            OllamaError: On transport failures or a missing/invalid embedding.
        """
        use_model = model if model is not None else self.model
        use_base = base_url if base_url is not None else self.base_url
        result = _request(use_base, "/api/embeddings", {"model": use_model, "prompt": text})
        embedding = result.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise OllamaError("Ollama returned an empty or invalid embedding.")
        return [float(value) for value in embedding]

    def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        base_url: str | None = None,
    ) -> list[list[float]]:
        """Return embedding vectors for ``texts`` via the batch ``/api/embed`` endpoint.

        Args:
            texts: Texts to embed, in order.
            model: Optional per-call embedding model override.
            base_url: Optional per-call base URL override.

        Returns:
            Embedding vectors in the same order as ``texts``.

        Raises:
            OllamaError: On transport failures, or if the response shape/count is invalid.
        """
        if not texts:
            return []
        use_model = model if model is not None else self.model
        use_base = base_url if base_url is not None else self.base_url
        result = _request(use_base, "/api/embed", {"model": use_model, "input": texts})
        embeddings = result.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Ollama returned an unexpected number of embeddings.")
        return [[float(value) for value in vector] for vector in embeddings]
