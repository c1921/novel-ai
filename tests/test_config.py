from __future__ import annotations

import os

from novel_cli.config import get_deepseek_base_url, load_project_config


def test_load_project_config_applies_defaults(workspace_dir, monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    config = load_project_config(workspace_dir)

    assert config.project_name == workspace_dir.name
    assert config.language == "zh-CN"
    assert config.model.provider == "deepseek"
    assert config.model.name == "deepseek-chat"
    assert config.paths.chapters == (workspace_dir / "chapters").resolve()
    assert config.context.story_so_far == (workspace_dir / "summaries" / "story-so-far.md").resolve()


def test_load_project_config_reads_yaml_and_env(workspace_dir, monkeypatch) -> None:
    (workspace_dir / "novel.yaml").write_text(
        "\n".join(
            [
                "project_name: demo",
                "model:",
                "  name: deepseek-reasoner",
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
        "DEEPSEEK_API_KEY=test-key\nDEEPSEEK_BASE_URL=https://example.test/v1\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    config = load_project_config(workspace_dir)

    assert config.project_name == "demo"
    assert config.model.name == "deepseek-reasoner"
    assert config.model.temperature == 0.2
    assert config.paths.chapters == (workspace_dir / "manuscript").resolve()
    assert config.context.style == (workspace_dir / "handbook" / "style.md").resolve()
    assert os.getenv("DEEPSEEK_API_KEY") == "test-key"
    assert get_deepseek_base_url() == "https://example.test/v1"
