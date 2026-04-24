from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path

from .errors import NovelCliError

DIRECTORIES = [
    "prompts",
    "docs",
    "chapters",
    "drafts",
    "summaries",
]

TEMPLATE_FILES = [
    ".gitignore",
    "novel.yaml",
    "AGENTS.md",
    "prompts/polish.md",
    "prompts/continue.md",
    "prompts/rewrite.md",
    "prompts/summarize.md",
    "docs/style.md",
    "docs/characters.md",
    "docs/worldbuilding.md",
    "docs/timeline.md",
    "docs/glossary.md",
    "summaries/story-so-far.md",
]


@dataclass(slots=True)
class InitResult:
    project_root: Path
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def init_project(project_root: Path) -> InitResult:
    project_root = project_root.resolve()
    result = InitResult(project_root=project_root)

    for relative_path in DIRECTORIES:
        _ensure_directory(project_root / relative_path, result)

    for relative_path in TEMPLATE_FILES:
        _write_template_file(project_root, Path(relative_path), result)

    return result


def _ensure_directory(path: Path, result: InitResult) -> None:
    if path.exists():
        result.skipped.append(path)
        return

    path.mkdir(parents=True, exist_ok=True)
    result.created.append(path)


def _write_template_file(project_root: Path, relative_path: Path, result: InitResult) -> None:
    destination = project_root / relative_path
    if destination.exists():
        result.skipped.append(destination)
        return

    template = files("novel_cli").joinpath("templates", "project", *relative_path.parts)
    try:
        content = template.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise NovelCliError(f"Missing bundled template: {relative_path}") from exc

    content = content.replace("{{PROJECT_NAME}}", project_root.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    result.created.append(destination)
