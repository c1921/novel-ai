from __future__ import annotations

import pytest

from novel_cli.cli import build_parser, main


def test_init_creates_project_files(workspace_dir, monkeypatch, capsys) -> None:
    monkeypatch.chdir(workspace_dir)

    exit_code = main(["init"])
    captured = capsys.readouterr()
    project_config = (workspace_dir / "novel.yaml").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "Initialized project" in captured.out
    assert "api:" in project_config
    assert "base_url: https://api.openai.com/v1" in project_config
    assert "provider" not in project_config
    assert "name: gpt-4.1-mini" in project_config
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "prompts" / "polish.md").exists()


def test_help_includes_init_config() -> None:
    assert "init-config" in build_parser().format_help()


def test_init_config_creates_user_config(user_config_file, capsys) -> None:
    exit_code = main(["init-config"])
    captured = capsys.readouterr()
    content = user_config_file.read_text(encoding="utf-8")

    assert exit_code == 0
    assert user_config_file.exists()
    assert "Created user config" in captured.out
    assert "api:" in content
    assert "base_url: https://api.openai.com/v1" in content
    assert "model:" in content
    assert "name: gpt-4.1-mini" in content
    assert "deepseek" not in content


def test_init_config_does_not_overwrite_existing(user_config_file, capsys) -> None:
    existing = "api:\n  base_url: https://custom.example/v1\n"
    user_config_file.parent.mkdir(parents=True, exist_ok=True)
    user_config_file.write_text(existing, encoding="utf-8")

    exit_code = main(["init-config"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert user_config_file.read_text(encoding="utf-8") == existing
    assert "Skipped existing user config" in captured.out


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
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: f"{mode} output")

    exit_code = main([mode, "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / expected_output).read_text(encoding="utf-8") == f"{mode} output"


def test_generation_versions_existing_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "drafts" / "001.polished.md").write_text("old", encoding="utf-8")
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "new")

    exit_code = main(["polish", "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / "drafts" / "001.polished.v2.md").read_text(encoding="utf-8") == "new"


def test_generation_warns_for_missing_optional_context(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "docs" / "worldbuilding.md").unlink()
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "output")

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Optional context file not found" in captured.err


def test_generation_uses_user_config_defaults(sample_project, user_config_file, monkeypatch) -> None:
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
    (sample_project / "novel.yaml").write_text("project_name: sample\n", encoding="utf-8")
    monkeypatch.chdir(sample_project)
    captured: dict[str, object] = {}

    def fake_call_api(**kwargs):
        captured["base_url"] = kwargs["base_url"]
        captured["model"] = kwargs["model"]
        captured["temperature"] = kwargs["temperature"]
        return "output"

    monkeypatch.setattr("novel_cli.cli.call_api", fake_call_api)

    exit_code = main(["polish", "chapters/001.md"])

    assert exit_code == 0
    assert captured == {
        "base_url": "https://global.example/v1",
        "model": "gpt-4.1-mini-global",
        "temperature": 0.4,
    }


def test_generation_prefers_project_values_over_user_config(sample_project, user_config_file, monkeypatch) -> None:
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
    monkeypatch.chdir(sample_project)
    captured: dict[str, object] = {}

    def fake_call_api(**kwargs):
        captured["base_url"] = kwargs["base_url"]
        captured["model"] = kwargs["model"]
        captured["temperature"] = kwargs["temperature"]
        return "output"

    monkeypatch.setattr("novel_cli.cli.call_api", fake_call_api)

    exit_code = main(["polish", "chapters/001.md"])

    assert exit_code == 0
    assert captured == {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
        "temperature": 0.7,
    }


def test_cli_returns_error_when_project_root_missing(workspace_dir, monkeypatch, capsys) -> None:
    monkeypatch.chdir(workspace_dir)

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Could not locate a novel project root" in captured.err


def test_cli_returns_error_when_chapter_missing(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "unused")

    exit_code = main(["summarize", "chapters/999.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Chapter file does not exist" in captured.err


def test_quiet_flag_is_parsed() -> None:
    parser = build_parser()
    args = parser.parse_args(["-q", "polish", "chapters/001.md"])
    assert args.quiet is True

    args = parser.parse_args(["--quiet", "polish", "chapters/001.md"])
    assert args.quiet is True

    args = parser.parse_args(["polish", "chapters/001.md"])
    assert args.quiet is False


def test_default_produces_step_output(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "生成的正文内容")

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[步骤 1/7] 检测项目" in captured.err
    assert "[步骤 2/7] 加载上下文" in captured.err
    assert "[步骤 3/7] 构建提示词" in captured.err
    assert "[步骤 4/7] 确定输出路径" in captured.err
    assert "[步骤 5/7] 调用 API" in captured.err
    assert "[步骤 6/7] 写入文件" in captured.err
    assert "Mode: polish" in captured.out
    assert "Output:" in captured.out


def test_quiet_suppresses_step_output(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "generated content")

    exit_code = main(["-q", "polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[步骤" not in captured.err
    assert "[步骤" not in captured.out
    assert "Mode: polish" in captured.out


def test_default_shows_api_and_response_info(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "生成的正文内容")

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "gpt-4.1-mini" in captured.err
    assert "https://api.openai.com/v1" in captured.err
    assert "温度" in captured.err
    assert "响应长度" in captured.err
    assert "提示词长度" in captured.err
