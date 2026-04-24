from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

from .context_loader import GenerationContext
from .errors import NovelCliError

SUPPORTED_MODES = {"polish", "continue", "summarize", "fill"}


@dataclass(slots=True)
class PromptBuildResult:
    prompt: str
    template_source: str


def build_prompt(context: GenerationContext) -> PromptBuildResult:
    if context.mode not in SUPPORTED_MODES:
        raise NovelCliError(f"Unsupported prompt mode: {context.mode}")

    template_text, template_source = _load_template(context)
    prompt = template_text
    for key, value in context.template_variables().items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)

    return PromptBuildResult(prompt=prompt, template_source=template_source)


def _load_template(context: GenerationContext) -> tuple[str, str]:
    project_template = context.config.paths.prompts / f"{context.mode}.md"
    if project_template.exists():
        return _read_text(project_template), str(project_template)

    built_in_template = files("novel_cli").joinpath("templates", "prompts", f"{context.mode}.md")
    try:
        return built_in_template.read_text(encoding="utf-8"), f"<built-in {context.mode} template>"
    except FileNotFoundError as exc:
        raise NovelCliError(
            f"Prompt template not found for mode `{context.mode}`.",
            "Create `prompts/<mode>.md` in the project or restore the built-in templates.",
        ) from exc


def _read_text(path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise NovelCliError(f"Failed to read prompt template: {path}", str(exc)) from exc
