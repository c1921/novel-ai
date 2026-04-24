from __future__ import annotations

import pytest

from novel_cli.api_client import call_api
from novel_cli.errors import NovelCliError


def test_call_api_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("NOVEL_API_KEY", raising=False)

    with pytest.raises(NovelCliError, match="Missing NOVEL_API_KEY"):
        call_api(prompt="hello", model="gpt-4.1-mini", temperature=0.7)
