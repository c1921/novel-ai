from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import os

from dotenv import load_dotenv
from platformdirs import user_config_path
import yaml

from .errors import NovelCliError

DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_MODEL_NAME = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BASE_URL = "https://api.openai.com/v1"


@dataclass(slots=True, frozen=True)
class ApiConfig:
    base_url: str


@dataclass(slots=True, frozen=True)
class ModelConfig:
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
    api: ApiConfig
    model: ModelConfig
    paths: PathConfig
    context: ContextConfig
    output_overwrite: bool


@dataclass(slots=True, frozen=True)
class UserConfig:
    base_url: str | None = None
    model: str | None = None
    temperature: float | None = None


@dataclass(slots=True, frozen=True)
class UserConfigInitResult:
    config_path: Path
    created: bool


@dataclass(slots=True, frozen=True)
class RuntimeConfigOverrides:
    model_name: str | None = None
    temperature: float | None = None


def load_project_config(
    project_root: Path,
    overrides: RuntimeConfigOverrides | None = None,
) -> ProjectConfig:
    project_root = project_root.resolve()
    _load_project_env(project_root)
    user_config = load_user_config()
    raw_config = _read_yaml(project_root / "novel.yaml")
    _validate_project_config_schema(raw_config)
    overrides = overrides or RuntimeConfigOverrides()

    project_name = str(raw_config.get("project_name") or project_root.name)
    language = str(raw_config.get("language") or DEFAULT_LANGUAGE)

    api_data = _ensure_dict(raw_config.get("api"), "api")
    model_data = _ensure_dict(raw_config.get("model"), "model")
    base_url = _resolve_base_url(api_data, user_config)
    model_name = overrides.model_name or _resolve_model_name(model_data, user_config)
    temperature = overrides.temperature if overrides.temperature is not None else _resolve_temperature(model_data, user_config)

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
        api=ApiConfig(base_url=base_url),
        model=ModelConfig(name=model_name, temperature=temperature),
        paths=paths,
        context=context,
        output_overwrite=output_overwrite,
    )


def get_api_base_url(project_root: Path | None = None) -> str:
    if project_root is None:
        return _resolve_base_url({}, load_user_config())

    project_root = project_root.resolve()
    _load_project_env(project_root)
    raw_config = _read_yaml(project_root / "novel.yaml")
    _validate_project_config_schema(raw_config)
    api_data = _ensure_dict(raw_config.get("api"), "api")
    return _resolve_base_url(api_data, load_user_config())


def get_user_config_path() -> Path:
    return Path(user_config_path("novel-cli", appauthor=False)) / "config.yaml"


def load_user_config(config_path: Path | None = None) -> UserConfig:
    path = config_path or get_user_config_path()
    raw_config = _read_yaml(path)
    _validate_user_config_schema(raw_config)
    api_data = _ensure_dict(raw_config.get("api"), "api")
    model_data = _ensure_dict(raw_config.get("model"), "model")

    return UserConfig(
        base_url=_optional_string(api_data.get("base_url"), "api.base_url"),
        model=_optional_string(model_data.get("name"), "model.name"),
        temperature=_optional_float(model_data.get("temperature"), "model.temperature"),
    )


def init_user_config(config_path: Path | None = None) -> UserConfigInitResult:
    path = (config_path or get_user_config_path()).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return UserConfigInitResult(config_path=path, created=False)

    template = files("novel_cli").joinpath("templates", "config", "config.yaml")
    try:
        content = template.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise NovelCliError("Missing bundled user config template.") from exc

    path.write_text(content, encoding="utf-8")
    return UserConfigInitResult(config_path=path, created=True)


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
        raise NovelCliError(f"{field_name} must be a mapping.")
    return value


def _parse_float(value: object, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise NovelCliError(f"{field_name} must be a number.") from exc


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise NovelCliError(f"{field_name} must be a string.")
    return value


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    return _parse_float(value, field_name)


def _resolve_base_url(api_data: dict[str, object], user_config: UserConfig) -> str:
    env_base_url = os.getenv("NOVEL_BASE_URL")
    if env_base_url:
        return env_base_url

    project_base_url = _optional_string(api_data.get("base_url"), "api.base_url")
    if project_base_url:
        return project_base_url

    if user_config.base_url:
        return user_config.base_url
    return DEFAULT_BASE_URL


def _resolve_model_name(model_data: dict[str, object], user_config: UserConfig) -> str:
    env_model = os.getenv("NOVEL_MODEL")
    if env_model:
        return env_model

    project_model = _optional_string(model_data.get("name"), "model.name")
    if project_model:
        return project_model

    if user_config.model:
        return user_config.model
    return DEFAULT_MODEL_NAME


def _resolve_temperature(model_data: dict[str, object], user_config: UserConfig) -> float:
    env_temperature = os.getenv("NOVEL_TEMPERATURE")
    if env_temperature:
        return _parse_float(env_temperature, "NOVEL_TEMPERATURE")
    if model_data.get("temperature") is not None:
        return _parse_float(model_data["temperature"], "model.temperature")
    if user_config.temperature is not None:
        return user_config.temperature
    return DEFAULT_TEMPERATURE


def _validate_project_config_schema(raw_config: dict[str, object]) -> None:
    if "provider" in raw_config:
        raise NovelCliError(
            "Legacy project config detected: `provider` has been removed.",
            "Update `novel.yaml` to use `api.base_url` and `model.name` instead.",
        )

    model_data = raw_config.get("model")
    if isinstance(model_data, dict) and "provider" in model_data:
        raise NovelCliError(
            "Legacy project config detected: `model.provider` has been removed.",
            "Remove `model.provider` and configure `api.base_url` plus `model.name` instead.",
        )


def _validate_user_config_schema(raw_config: dict[str, object]) -> None:
    if "deepseek" in raw_config:
        raise NovelCliError(
            "Legacy user config detected: `deepseek` has been removed.",
            "Update your user config to use `api.base_url`, `model.name`, and `model.temperature`.",
        )
