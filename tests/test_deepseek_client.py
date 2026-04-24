from __future__ import annotations

import pytest

from novel_cli.deepseek_client import call_deepseek
from novel_cli.errors import NovelCliError


def test_call_deepseek_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(NovelCliError, match="Missing DEEPSEEK_API_KEY"):
        call_deepseek(prompt="hello", model="deepseek-chat", temperature=0.7)
