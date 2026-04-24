from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from novel_cli.api_client import call_api, call_api_stream
from novel_cli.errors import NovelCliError


def test_call_api_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("NOVEL_API_KEY", raising=False)

    with pytest.raises(NovelCliError, match="Missing NOVEL_API_KEY"):
        call_api(prompt="hello", model="gpt-4.1-mini", temperature=0.7)


def test_call_api_stream_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("NOVEL_API_KEY", raising=False)

    with pytest.raises(NovelCliError, match="Missing NOVEL_API_KEY"):
        next(call_api_stream(prompt="hello", model="gpt-4.1-mini", temperature=0.7))


def test_call_api_stream_yields_chunks(monkeypatch) -> None:
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta.content = "Hello"

    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta.content = " world"

    mock_chunk3 = MagicMock()
    mock_chunk3.choices = [MagicMock()]
    mock_chunk3.choices[0].delta.content = None  # should be skipped

    mock_chunk4 = MagicMock()
    mock_chunk4.choices = [MagicMock()]
    mock_chunk4.choices[0].delta.content = "!"

    mock_response = [mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    def fake_build_client(*args, **kwargs):
        return mock_client, [{"role": "user", "content": "hello"}]

    monkeypatch.setattr("novel_cli.api_client._build_client_and_messages", fake_build_client)

    result = list(call_api_stream(prompt="hello", model="test-model", temperature=0.7))

    assert result == ["Hello", " world", "!"]

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is True


def test_call_api_stream_handles_api_error(monkeypatch) -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("Connection refused")

    def fake_build_client(*args, **kwargs):
        return mock_client, [{"role": "user", "content": "hello"}]

    monkeypatch.setattr("novel_cli.api_client._build_client_and_messages", fake_build_client)

    with pytest.raises(NovelCliError, match="API request failed"):
        list(call_api_stream(prompt="hello", model="test-model", temperature=0.7))


def test_call_api_stream_empty_response(monkeypatch) -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = []

    def fake_build_client(*args, **kwargs):
        return mock_client, [{"role": "user", "content": "hello"}]

    monkeypatch.setattr("novel_cli.api_client._build_client_and_messages", fake_build_client)

    with pytest.raises(NovelCliError, match="API returned empty content"):
        list(call_api_stream(prompt="hello", model="test-model", temperature=0.7))
