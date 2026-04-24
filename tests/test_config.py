from __future__ import annotations

import os

import pytest

from novel_cli.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL_NAME,
    DEFAULT_TEMPERATURE,
    RuntimeConfigOverrides,
    get_api_base_url,
    load_project_config,
)
from novel_cli.errors import NovelCliError


def test_load_project_config_applies_defaults(workspace_dir, monkeypatch) -> None:
    monkeypatch.delenv("NOVEL_MODEL", raising=False)
    monkeypatch.delenv("NOVEL_BASE_URL", raising=False)
    monkeypatch.delenv("NOVEL_TEMPERATURE", raising=False)
    config = load_project_config(workspace_dir)

    assert config.project_name == workspace_dir.name
    assert config.language == "zh-CN"
    assert config.api.base_url == DEFAULT_BASE_URL
    assert config.model.name == DEFAULT_MODEL_NAME
    assert config.model.temperature == DEFAULT_TEMPERATURE
    assert config.paths.chapters == (workspace_dir / "chapters").resolve()
    assert config.context.story_so_far == (workspace_dir / "summaries" / "story-so-far.md").resolve()


def test_load_project_config_reads_yaml_and_env(workspace_dir, monkeypatch) -> None:
    (workspace_dir / "novel.yaml").write_text(
        "\n".join(
            [
                "project_name: demo",
                "api:",
                "  base_url: https://project.example/v1",
                "model:",
                "  name: gpt-4.1",
                "  temperature: 0.2",
                "paths:",
                "  chapters: manuscript",
                "context:",
                "  style: handbook/style.md",
            ]
        ),
        encoding="utf-8",
    )
    (workspace_dir / ".env").write_text(
        "\n".join(
            [
                "NOVEL_API_KEY=test-key",
                "NOVEL_BASE_URL=https://env.example/v1",
                "NOVEL_MODEL=gpt-4.1-nano",
                "NOVEL_TEMPERATURE=0.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("NOVEL_API_KEY", raising=False)
    monkeypatch.delenv("NOVEL_BASE_URL", raising=False)
    monkeypatch.delenv("NOVEL_MODEL", raising=False)
    monkeypatch.delenv("NOVEL_TEMPERATURE", raising=False)

    config = load_project_config(workspace_dir)

    assert config.project_name == "demo"
    assert config.api.base_url == "https://env.example/v1"
    assert config.model.name == "gpt-4.1-nano"
    assert config.model.temperature == 0.1
    assert config.paths.chapters == (workspace_dir / "manuscript").resolve()
    assert config.context.style == (workspace_dir / "handbook" / "style.md").resolve()
    assert os.getenv("NOVEL_API_KEY") == "test-key"
    assert get_api_base_url(workspace_dir) == "https://env.example/v1"


def test_load_project_config_reads_user_config_defaults(workspace_dir, user_config_file, monkeypatch) -> None:
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text(
        "\n".join(
            [
                "api:",
                "  base_url: https://global.example/v1",
                "",
                "model:",
                "  name: gpt-4.1-mini-global",
                "  temperature: 0.4",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("NOVEL_MODEL", raising=False)
    monkeypatch.delenv("NOVEL_BASE_URL", raising=False)
    monkeypatch.delenv("NOVEL_TEMPERATURE", raising=False)

    config = load_project_config(workspace_dir)

    assert config.api.base_url == "https://global.example/v1"
    assert config.model.name == "gpt-4.1-mini-global"
    assert config.model.temperature == 0.4
    assert get_api_base_url(workspace_dir) == "https://global.example/v1"


def test_load_project_config_prefers_project_values_over_user_config(
    workspace_dir,
    user_config_file,
    monkeypatch,
) -> None:
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text(
        "\n".join(
            [
                "api:",
                "  base_url: https://global.example/v1",
                "",
                "model:",
                "  name: gpt-4.1-mini-global",
                "  temperature: 0.4",
            ]
        ),
        encoding="utf-8",
    )
    (workspace_dir / "novel.yaml").write_text(
        "\n".join(
            [
                "project_name: demo",
                "api:",
                "  base_url: https://project.example/v1",
                "model:",
                "  name: gpt-4.1-mini-project",
                "  temperature: 0.2",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("NOVEL_MODEL", raising=False)
    monkeypatch.delenv("NOVEL_BASE_URL", raising=False)
    monkeypatch.delenv("NOVEL_TEMPERATURE", raising=False)

    config = load_project_config(workspace_dir)

    assert config.api.base_url == "https://project.example/v1"
    assert config.model.name == "gpt-4.1-mini-project"
    assert config.model.temperature == 0.2


def test_load_project_config_applies_environment_precedence(workspace_dir, user_config_file, monkeypatch) -> None:
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text(
        "\n".join(
            [
                "api:",
                "  base_url: https://global.example/v1",
                "",
                "model:",
                "  name: gpt-4.1-mini-global",
                "  temperature: 0.4",
            ]
        ),
        encoding="utf-8",
    )
    (workspace_dir / "novel.yaml").write_text(
        "\n".join(
            [
                "project_name: demo",
                "api:",
                "  base_url: https://project.example/v1",
                "model:",
                "  name: gpt-4.1-mini-project",
                "  temperature: 0.2",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("NOVEL_MODEL", "gpt-4.1-mini-env")
    monkeypatch.setenv("NOVEL_BASE_URL", "https://env.example/v1")
    monkeypatch.setenv("NOVEL_TEMPERATURE", "0.1")

    config = load_project_config(workspace_dir)

    assert config.api.base_url == "https://env.example/v1"
    assert config.model.name == "gpt-4.1-mini-env"
    assert config.model.temperature == 0.1
    assert get_api_base_url(workspace_dir) == "https://env.example/v1"


def test_load_project_config_applies_runtime_overrides(workspace_dir, monkeypatch) -> None:
    monkeypatch.setenv("NOVEL_MODEL", "gpt-4.1-mini-env")
    monkeypatch.setenv("NOVEL_TEMPERATURE", "0.1")

    config = load_project_config(
        workspace_dir,
        overrides=RuntimeConfigOverrides(
            model_name="gpt-4.1-cli",
            temperature=0.9,
        ),
    )

    assert config.model.name == "gpt-4.1-cli"
    assert config.model.temperature == 0.9


def test_load_user_config_errors_for_invalid_structure(user_config_file) -> None:
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text("api: []\n", encoding="utf-8")

    with pytest.raises(NovelCliError, match="api must be a mapping"):
        load_project_config(user_config_file.parent.parent)


def test_load_user_config_errors_for_legacy_deepseek_key(user_config_file) -> None:
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text("deepseek:\n  model: legacy\n", encoding="utf-8")

    with pytest.raises(NovelCliError, match="Legacy user config detected"):
        load_project_config(user_config_file.parent.parent)


def test_load_project_config_errors_for_legacy_provider(workspace_dir) -> None:
    (workspace_dir / "novel.yaml").write_text(
        "\n".join(
            [
                "model:",
                "  provider: deepseek",
                "  name: legacy-model",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(NovelCliError, match="model\\.provider"):
        load_project_config(workspace_dir)
