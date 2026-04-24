from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv
import yaml

from .errors import NovelCliError

DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_MODEL_PROVIDER = "deepseek"
DEFAULT_MODEL_NAME = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BASE_URL = "https://api.deepseek.com"


@dataclass(slots=True, frozen=True)
class ModelConfig:
    provider: str
    name: str
    temperature: float


@dataclass(slots=True, frozen=True)
class PathConfig:
    chapters: Path
    drafts: Path
    summaries: Path
    prompts: Path
    docs: Path


@dataclass(slots=True, frozen=True)
class ContextConfig:
    style: Path
    characters: Path
    worldbuilding: Path
    timeline: Path
    glossary: Path
    story_so_far: Path


@dataclass(slots=True, frozen=True)
class ProjectConfig:
    project_root: Path
    project_name: str
    language: str
    model: ModelConfig
    paths: PathConfig
    context: ContextConfig
    output_overwrite: bool


def load_project_config(project_root: Path) -> ProjectConfig:
    project_root = project_root.resolve()
    _load_project_env(project_root)
    raw_config = _read_yaml(project_root / "novel.yaml")

    project_name = str(raw_config.get("project_name") or project_root.name)
    language = str(raw_config.get("language") or DEFAULT_LANGUAGE)

    model_data = _ensure_dict(raw_config.get("model"), "model")
    provider = str(model_data.get("provider") or DEFAULT_MODEL_PROVIDER)
    if provider != DEFAULT_MODEL_PROVIDER:
        raise NovelCliError(
            f"Unsupported model provider: {provider}.",
            "Only the DeepSeek provider is supported in the MVP.",
        )

    model_name = str(model_data.get("name") or os.getenv("DEEPSEEK_MODEL") or DEFAULT_MODEL_NAME)
    temperature = _parse_float(model_data.get("temperature", DEFAULT_TEMPERATURE), "model.temperature")

    paths_data = _ensure_dict(raw_config.get("paths"), "paths")
    paths = PathConfig(
        chapters=_resolve_path(project_root, paths_data.get("chapters") or "chapters"),
        drafts=_resolve_path(project_root, paths_data.get("drafts") or "drafts"),
        summaries=_resolve_path(project_root, paths_data.get("summaries") or "summaries"),
        prompts=_resolve_path(project_root, paths_data.get("prompts") or "prompts"),
        docs=_resolve_path(project_root, paths_data.get("docs") or "docs"),
    )

    context_data = _ensure_dict(raw_config.get("context"), "context")
    context = ContextConfig(
        style=_resolve_path(project_root, context_data.get("style") or "docs/style.md"),
        characters=_resolve_path(project_root, context_data.get("characters") or "docs/characters.md"),
        worldbuilding=_resolve_path(project_root, context_data.get("worldbuilding") or "docs/worldbuilding.md"),
        timeline=_resolve_path(project_root, context_data.get("timeline") or "docs/timeline.md"),
        glossary=_resolve_path(project_root, context_data.get("glossary") or "docs/glossary.md"),
        story_so_far=_resolve_path(project_root, context_data.get("story_so_far") or "summaries/story-so-far.md"),
    )

    output_data = _ensure_dict(raw_config.get("output"), "output")
    output_overwrite = bool(output_data.get("overwrite", False))

    return ProjectConfig(
        project_root=project_root,
        project_name=project_name,
        language=language,
        model=ModelConfig(provider=provider, name=model_name, temperature=temperature),
        paths=paths,
        context=context,
        output_overwrite=output_overwrite,
    )


def get_deepseek_base_url() -> str:
    return os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL


def _load_project_env(project_root: Path) -> None:
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)


def _read_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise NovelCliError(f"Failed to read {path}.", str(exc)) from exc
    except yaml.YAMLError as exc:
        raise NovelCliError(f"Failed to parse {path}.", str(exc)) from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise NovelCliError(f"{path} must contain a YAML mapping at the top level.")
    return data


def _resolve_path(project_root: Path, raw_path: object) -> Path:
    if not isinstance(raw_path, str):
        raise NovelCliError(f"Expected a string path value, got: {raw_path!r}.")

    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (project_root / candidate).resolve()


def _ensure_dict(value: object, field_name: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise NovelCliError(f"{field_name} must be a mapping in novel.yaml.")
    return value


def _parse_float(value: object, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise NovelCliError(f"{field_name} must be a number.") from exc
