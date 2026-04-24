from __future__ import annotations

import pytest

from novel_cli.cli import main


def test_init_creates_project_files(workspace_dir, monkeypatch, capsys) -> None:
    monkeypatch.chdir(workspace_dir)

    exit_code = main(["init"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Initialized project" in captured.out
    assert (workspace_dir / "novel.yaml").exists()
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "prompts" / "polish.md").exists()


@pytest.mark.parametrize(
    ("mode", "expected_output"),
    [
        ("polish", "drafts/001.polished.md"),
        ("continue", "drafts/001.continued.md"),
        ("summarize", "summaries/001.md"),
    ],
)
def test_generation_commands_write_outputs(
    sample_project,
    monkeypatch,
    mode: str,
    expected_output: str,
) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr(
        "novel_cli.cli.call_deepseek",
        lambda prompt, model, temperature, system_prompt=None: f"{mode} output",
    )

    exit_code = main([mode, "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / expected_output).read_text(encoding="utf-8") == f"{mode} output"


def test_generation_versions_existing_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "drafts" / "001.polished.md").write_text("old", encoding="utf-8")
    monkeypatch.setattr(
        "novel_cli.cli.call_deepseek",
        lambda prompt, model, temperature, system_prompt=None: "new",
    )

    exit_code = main(["polish", "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / "drafts" / "001.polished.v2.md").read_text(encoding="utf-8") == "new"


def test_generation_warns_for_missing_optional_context(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "docs" / "worldbuilding.md").unlink()
    monkeypatch.setattr(
        "novel_cli.cli.call_deepseek",
        lambda prompt, model, temperature, system_prompt=None: "output",
    )

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Optional context file not found" in captured.err


def test_cli_returns_error_when_project_root_missing(workspace_dir, monkeypatch, capsys) -> None:
    monkeypatch.chdir(workspace_dir)

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Could not locate a novel project root" in captured.err


def test_cli_returns_error_when_chapter_missing(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr(
        "novel_cli.cli.call_deepseek",
        lambda prompt, model, temperature, system_prompt=None: "unused",
    )

    exit_code = main(["summarize", "chapters/999.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Chapter file does not exist" in captured.err
