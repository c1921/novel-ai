from __future__ import annotations

import pytest

from novel_cli.context_loader import load_generation_context
from novel_cli.errors import NovelCliError
from novel_cli.project_initializer import init_project
from novel_cli.prompt_builder import build_prompt, load_prompt_template


def test_build_prompt_prefers_project_template(workspace_dir) -> None:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("章节正文。", encoding="utf-8")
    (workspace_dir / "prompts" / "polish.md").write_text("CUSTOM {{CHAPTER_TEXT}}", encoding="utf-8")

    context = load_generation_context(workspace_dir, "chapters/001.md", "polish")
    result = build_prompt(context)

    assert result.template_source == str((workspace_dir / "prompts" / "polish.md"))
    assert result.prompt == "CUSTOM 章节正文。"


def test_build_prompt_falls_back_to_builtin_template(workspace_dir) -> None:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("章节正文。", encoding="utf-8")
    (workspace_dir / "prompts" / "polish.md").unlink()

    context = load_generation_context(workspace_dir, "chapters/001.md", "polish")
    result = build_prompt(context)

    assert result.template_source == "<built-in polish template>"
    assert "章节正文。" in result.prompt
    assert "# 润色任务" in result.prompt


def test_build_prompt_errors_when_no_template_exists(workspace_dir, monkeypatch) -> None:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("章节正文。", encoding="utf-8")
    (workspace_dir / "prompts" / "polish.md").unlink()
    missing_root = workspace_dir / "missing-package-data"
    missing_root.mkdir()
    context = load_generation_context(workspace_dir, "chapters/001.md", "polish")
    monkeypatch.setattr("novel_cli.prompt_builder.files", lambda _package: missing_root)

    with pytest.raises(NovelCliError, match="Prompt template not found"):
        build_prompt(context)


def test_build_prompt_uses_explicit_template_path(workspace_dir) -> None:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("章节正文。", encoding="utf-8")
    template_path = workspace_dir / "custom-rewrite.md"
    template_path.write_text("OVERRIDE {{INSTRUCTION}} {{CHAPTER_TEXT}}", encoding="utf-8")

    context = load_generation_context(
        workspace_dir,
        "chapters/001.md",
        "rewrite",
        instruction="改成第一人称",
    )
    result = build_prompt(context, template_path=template_path)

    assert result.template_source == str(template_path)
    assert result.prompt == "OVERRIDE 改成第一人称 章节正文。"


def test_load_prompt_template_errors_for_missing_explicit_path(workspace_dir) -> None:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("章节正文。", encoding="utf-8")
    config = load_generation_context(workspace_dir, "chapters/001.md", "polish").config

    with pytest.raises(NovelCliError, match="Prompt template does not exist"):
        load_prompt_template(config, "polish", template_path=workspace_dir / "missing.md")
