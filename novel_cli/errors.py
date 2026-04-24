from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NovelCliError(Exception):
    message: str
    hint: str | None = None

    def __str__(self) -> str:
        return self.message
