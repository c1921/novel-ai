from __future__ import annotations

import os
from collections.abc import Generator

from .config import get_api_base_url
from .errors import NovelCliError


def _build_client_and_messages(
    prompt: str,
    model: str,
    temperature: float,
    system_prompt: str | None = None,
    base_url: str | None = None,
) -> tuple:
    api_key = os.getenv("NOVEL_API_KEY")
    if not api_key:
        raise NovelCliError(
            "Missing NOVEL_API_KEY.",
            "Set `NOVEL_API_KEY` in your environment or project `.env` file.",
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise NovelCliError(
            "Missing dependency `openai`.",
            "Install project dependencies before invoking the API client.",
        ) from exc

    client = OpenAI(api_key=api_key, base_url=base_url or get_api_base_url())
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    return client, messages


def call_api(
    prompt: str,
    model: str,
    temperature: float,
    system_prompt: str | None = None,
    base_url: str | None = None,
) -> str:
    client, messages = _build_client_and_messages(
        prompt, model, temperature, system_prompt, base_url,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
        )
    except Exception as exc:
        raise NovelCliError(
            f"API request failed: {exc}",
            "Check `NOVEL_API_KEY`, `NOVEL_BASE_URL`, network access, and the model name.",
        ) from exc

    text = _extract_response_text(response)
    if not text:
        raise NovelCliError("API returned empty content.")
    return text


def call_api_stream(
    prompt: str,
    model: str,
    temperature: float,
    system_prompt: str | None = None,
    base_url: str | None = None,
) -> Generator[str, None, None]:
    client, messages = _build_client_and_messages(
        prompt, model, temperature, system_prompt, base_url,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
            stream=True,
        )
    except Exception as exc:
        raise NovelCliError(
            f"API request failed: {exc}",
            "Check `NOVEL_API_KEY`, `NOVEL_BASE_URL`, network access, and the model name.",
        ) from exc

    yielded = False
    try:
        for chunk in response:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yielded = True
                yield content
    except Exception as exc:
        raise NovelCliError(
            f"API request failed: {exc}",
            "Check `NOVEL_API_KEY`, `NOVEL_BASE_URL`, network access, and the model name.",
        ) from exc

    if not yielded:
        raise NovelCliError("API returned empty content.")


def _extract_response_text(response) -> str:
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise NovelCliError("API returned an unexpected response shape.") from exc

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(text)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(part.strip() for part in parts if part.strip())

    return str(content).strip()
