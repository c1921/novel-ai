from __future__ import annotations

from pathlib import Path

from .config import ProjectConfig

MODE_OUTPUT_NAMES = {
    "polish": ("drafts", ".polished.md"),
    "continue": ("drafts", ".continued.md"),
    "summarize": ("summaries", ".md"),
    "fill": ("drafts", ".filled.md"),
}


def determine_output_path(config: ProjectConfig, chapter_path: Path, mode: str) -> Path:
    destination_group, suffix = MODE_OUTPUT_NAMES[mode]
    base_name = chapter_path.stem

    if destination_group == "drafts":
        base_path = config.paths.drafts / f"{base_name}{suffix}"
    else:
        base_path = config.paths.summaries / f"{base_name}{suffix}"

    if config.output_overwrite:
        return base_path
    return next_available_path(base_path)


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path

    version = 2
    while True:
        candidate = path.with_name(f"{path.stem}.v{version}{path.suffix}")
        if not candidate.exists():
            return candidate
        version += 1


def write_output_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
