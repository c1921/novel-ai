from __future__ import annotations

from pathlib import Path

from .errors import NovelCliError


def detect_project_root(start_path: Path | None = None) -> Path:
    start = (start_path or Path.cwd()).resolve()
    current = start if start.is_dir() else start.parent

    for candidate in (current, *current.parents):
        if (candidate / "novel.yaml").is_file():
            return candidate

    if (current / "chapters").is_dir():
        return current

    raise NovelCliError(
        "Could not locate a novel project root.",
        "Run `novel init` in your project directory or create a `novel.yaml` file.",
    )
