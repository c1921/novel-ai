from __future__ import annotations

from pathlib import Path

from .config import ProjectConfig

MODE_OUTPUT_NAMES = {
    "polish": ("drafts", ".polished.md"),
    "continue": ("drafts", ".continued.md"),
    "rewrite": ("drafts", ".rewritten.md"),
    "summarize": ("summaries", ".md"),
    "fill": ("drafts", ".filled.md"),
}


def determine_output_path(
    config: ProjectConfig,
    chapter_path: Path,
    mode: str,
    *,
    explicit_output_path: Path | None = None,
    overwrite: bool | None = None,
) -> Path:
    base_path = explicit_output_path or _default_output_path(config, chapter_path, mode)
    base_path = base_path.resolve()

    _validate_output_path(config, base_path)

    effective_overwrite = config.output_overwrite if overwrite is None else overwrite
    if effective_overwrite:
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


def resolve_path_from_project_root(project_root: Path, raw_path: str | Path) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve()


def _default_output_path(config: ProjectConfig, chapter_path: Path, mode: str) -> Path:
    destination_group, suffix = MODE_OUTPUT_NAMES[mode]
    base_name = chapter_path.stem

    if destination_group == "drafts":
        return config.paths.drafts / f"{base_name}{suffix}"
    return config.paths.summaries / f"{base_name}{suffix}"


def _validate_output_path(config: ProjectConfig, output_path: Path) -> None:
    if output_path.is_relative_to(config.paths.chapters.resolve()):
        from .errors import NovelCliError

        raise NovelCliError(
            f"Refusing to write output inside chapters/: {output_path}",
            "Use `--out` with a path outside `chapters/` or rely on the default drafts/summaries output.",
        )
