from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .config import ProjectConfig
from .context_loader import GenerationContext
from .errors import NovelCliError

SUPPORTED_MODES = {"polish", "continue", "summarize", "fill", "rewrite"}


@dataclass(slots=True)
class PromptBuildResult:
    prompt: str
    template_source: str


@dataclass(slots=True)
class PromptTemplate:
    text: str
    source: str


def build_prompt(
    context: GenerationContext,
    template_path: Path | None = None,
) -> PromptBuildResult:
    if context.mode not in SUPPORTED_MODES:
        raise NovelCliError(f"Unsupported prompt mode: {context.mode}")

    template = load_prompt_template(
        context.config,
        context.mode,
        template_path=template_path,
    )
    prompt = template.text
    for key, value in context.template_variables().items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)

    return PromptBuildResult(prompt=prompt, template_source=template.source)


def load_prompt_template(
    config: ProjectConfig,
    mode: str,
    *,
    template_path: Path | None = None,
) -> PromptTemplate:
    if mode not in SUPPORTED_MODES:
        raise NovelCliError(f"Unsupported prompt mode: {mode}")

    if template_path is not None:
        if not template_path.exists():
            raise NovelCliError(
                f"Prompt template does not exist: {template_path}",
                "Pass an existing template file to `--prompt`.",
            )
        return PromptTemplate(text=_read_text(template_path), source=str(template_path))

    project_template = config.paths.prompts / f"{mode}.md"
    if project_template.exists():
        return PromptTemplate(text=_read_text(project_template), source=str(project_template))

    built_in_template = files("novel_cli").joinpath("templates", "prompts", f"{mode}.md")
    try:
        return PromptTemplate(
            text=built_in_template.read_text(encoding="utf-8"),
            source=f"<built-in {mode} template>",
        )
    except FileNotFoundError as exc:
        raise NovelCliError(
            f"Prompt template not found for mode `{mode}`.",
            "Create `prompts/<mode>.md` in the project or restore the built-in templates.",
        ) from exc


def _read_text(path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NovelCliError(f"Failed to read prompt template: {path}", str(exc)) from exc
