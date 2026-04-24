from __future__ import annotations

from pathlib import Path

from .errors import NovelCliError


def resolve_project_root(
    project_path: str | Path | None,
    *,
    start_path: Path | None = None,
) -> Path:
    if project_path is None:
        return detect_project_root(start_path)

    start = (start_path or Path.cwd()).resolve()
    candidate = Path(project_path)
    if not candidate.is_absolute():
        candidate = start / candidate

    candidate = candidate.resolve()
    if not candidate.exists():
        raise NovelCliError(
            f"Project path does not exist: {candidate}",
            "Pass an existing project root directory to `--project`.",
        )
    if not candidate.is_dir():
        raise NovelCliError(
            f"Project path is not a directory: {candidate}",
            "Pass a project root directory to `--project`, not a file path.",
        )
    return candidate


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
