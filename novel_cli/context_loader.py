from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import ProjectConfig, load_project_config
from .errors import NovelCliError

OPTIONAL_CONTEXT_FILES = {
    "STYLE_GUIDE": "style",
    "CHARACTERS": "characters",
    "WORLDBUILDING": "worldbuilding",
    "TIMELINE": "timeline",
    "GLOSSARY": "glossary",
    "STORY_SO_FAR": "story_so_far",
}


GAP_MARKER = "<!-- GAP -->"


@dataclass(slots=True)
class GenerationContext:
    mode: str
    config: ProjectConfig
    chapter_path: Path
    chapter_text: str
    sections: dict[str, str]
    warnings: list[str]
    instruction: str = ""
    before_gap: str = ""
    after_gap: str = ""

    def template_variables(self) -> dict[str, str]:
        result: dict[str, str] = {
            "CHAPTER_TEXT": self.chapter_text,
            "INSTRUCTION": self.instruction,
            **self.sections,
        }
        if self.mode == "fill":
            result["BEFORE_GAP"] = self.before_gap
            result["AFTER_GAP"] = self.after_gap
        return result


def load_generation_context(
    project_root: Path,
    chapter_file: str | Path,
    mode: str,
    *,
    instruction: str = "",
    config: ProjectConfig | None = None,
) -> GenerationContext:
    config = config or load_project_config(project_root)
    chapter_path = _resolve_chapter_path(config, chapter_file)
    chapter_text = _read_required_text(chapter_path, "chapter")

    warnings: list[str] = []
    sections: dict[str, str] = {}
    for template_key, attribute in OPTIONAL_CONTEXT_FILES.items():
        path = getattr(config.context, attribute)
        if path.exists():
            sections[template_key] = _read_required_text(path, attribute)
        else:
            sections[template_key] = ""
            warnings.append(f"Optional context file not found: {path}")

    before_gap = ""
    after_gap = ""
    if mode == "fill":
        if GAP_MARKER not in chapter_text:
            raise NovelCliError(
                f"Fill marker `{GAP_MARKER}` not found in chapter.",
                "Insert `<!-- GAP -->` between two paragraphs to mark where content should be filled.",
            )
        parts = chapter_text.split(GAP_MARKER)
        before_gap = parts[0].strip()
        after_gap = parts[-1].strip()
        if len(parts) > 2:
            warnings.append(
                f"Multiple `{GAP_MARKER}` markers found. Using the first one; "
                f"{len(parts) - 1} markers ignored."
            )

    return GenerationContext(
        mode=mode,
        config=config,
        chapter_path=chapter_path,
        chapter_text=chapter_text,
        sections=sections,
        warnings=warnings,
        instruction=instruction,
        before_gap=before_gap,
        after_gap=after_gap,
    )


def _resolve_chapter_path(config: ProjectConfig, chapter_file: str | Path) -> Path:
    raw_path = Path(chapter_file)
    if not raw_path.is_absolute():
        raw_path = config.project_root / raw_path

    chapter_path = raw_path.resolve()
    if not chapter_path.exists():
        raise NovelCliError(
            f"Chapter file does not exist: {chapter_path}",
            "Pass a path relative to the project root, for example `chapters/003.md`.",
        )
    if not chapter_path.is_file():
        raise NovelCliError(f"Chapter path is not a file: {chapter_path}")

    return chapter_path


def _read_required_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NovelCliError(f"Failed to read {label} file: {path}", str(exc)) from exc
