from __future__ import annotations

from collections.abc import Generator
import json

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
    assert (workspace_dir / "prompts" / "rewrite.md").exists()


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
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter([f"{mode} output"]),
    )

    exit_code = main([mode, "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / expected_output).read_text(encoding="utf-8") == f"{mode} output"


def test_generation_versions_existing_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "drafts" / "001.polished.md").write_text("old", encoding="utf-8")
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "new")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["new"]),
    )

    exit_code = main(["polish", "chapters/001.md"])

    assert exit_code == 0
    assert (sample_project / "drafts" / "001.polished.v2.md").read_text(encoding="utf-8") == "new"


def test_generation_warns_for_missing_optional_context(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "docs" / "worldbuilding.md").unlink()
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "output")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["output"]),
    )

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

    def fake_call_api_stream(**kwargs):
        captured["base_url"] = kwargs["base_url"]
        captured["model"] = kwargs["model"]
        captured["temperature"] = kwargs["temperature"]
        yield "output"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

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

    def fake_call_api_stream(**kwargs):
        captured["base_url"] = kwargs["base_url"]
        captured["model"] = kwargs["model"]
        captured["temperature"] = kwargs["temperature"]
        yield "output"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

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
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["unused"]))

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
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["生成的正文内容"]),
    )

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[步骤 1/7] 检测项目" in captured.err
    assert "[步骤 2/7] 加载上下文" in captured.err
    assert "[步骤 3/7] 构建提示词" in captured.err
    assert "[步骤 4/7] 确定输出路径" in captured.err
    assert "调用 API" in captured.err
    assert "[步骤 6/7] 写入文件" in captured.err
    assert "Mode: polish" in captured.out
    assert "Output:" in captured.out


def test_quiet_suppresses_step_output(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "generated content")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["generated content"]),
    )

    exit_code = main(["-q", "polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[步骤" not in captured.err
    assert "[步骤" not in captured.out
    assert "Mode: polish" in captured.out


def test_default_shows_api_and_response_info(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "生成的正文内容")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["生成的正文内容"]),
    )

    exit_code = main(["polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "gpt-4.1-mini" in captured.err
    assert "https://api.openai.com/v1" in captured.err
    assert "温度" in captured.err
    assert "响应长度" in captured.err
    assert "提示词长度" in captured.err


def test_no_stream_flag_is_parsed() -> None:
    parser = build_parser()
    args = parser.parse_args(["--no-stream", "polish", "chapters/001.md"])
    assert args.no_stream is True

    args = parser.parse_args(["polish", "chapters/001.md"])
    assert args.no_stream is False


def test_no_stream_uses_blocking_call(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    call_api_called: list[bool] = []

    def fake_call_api(**kwargs):
        call_api_called.append(True)
        return "non-streaming output"

    monkeypatch.setattr("novel_cli.cli.call_api", fake_call_api)

    exit_code = main(["--no-stream", "polish", "chapters/001.md"])

    assert exit_code == 0
    assert call_api_called == [True]
    output = sample_project / "drafts" / "001.polished.md"
    assert output.read_text("utf-8") == "non-streaming output"


def test_quiet_suppresses_progress_but_not_streaming(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)

    def fake_call_api_stream(**kwargs) -> Generator[str, None, None]:
        yield "quiet"
        yield " streamed"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

    exit_code = main(["-q", "polish", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[步骤" not in captured.err
    assert "quiet streamed" in captured.out


def test_fill_writes_assembled_output(sample_project, monkeypatch) -> None:
    # Create a chapter with gap marker
    gap_chapter = sample_project / "chapters" / "001.md"
    gap_chapter.write_text(
        "这是前段的内容。\n\n<!-- GAP -->\n\n这是后段的内容。",
        encoding="utf-8",
    )
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "这是填补的过渡内容。")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["这是填补的过渡内容。"]),
    )

    exit_code = main(["fill", "chapters/001.md"])

    assert exit_code == 0
    output = sample_project / "drafts" / "001.filled.md"
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "这是前段的内容。" in content
    assert "这是填补的过渡内容。" in content
    assert "这是后段的内容。" in content


def test_fill_errors_without_gap_marker(sample_project, monkeypatch, capsys) -> None:
    # No gap marker in chapter
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "unused")
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["unused"]))

    exit_code = main(["fill", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "GAP" in captured.err


def test_rewrite_requires_instruction(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)

    exit_code = main(["rewrite", "chapters/001.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--instruction" in captured.err


def test_rewrite_writes_default_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "rewrite output")
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["rewrite output"]))

    exit_code = main(["rewrite", "chapters/001.md", "--instruction", "改成第一人称"])

    assert exit_code == 0
    assert (sample_project / "drafts" / "001.rewritten.md").read_text(encoding="utf-8") == "rewrite output"


def test_instruction_is_injected_into_prompt(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    captured: dict[str, str] = {}

    def fake_call_api_stream(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        yield "output"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

    exit_code = main(["polish", "chapters/001.md", "--instruction", "语言更冷峻"])

    assert exit_code == 0
    assert "语言更冷峻" in captured["prompt"]


def test_cli_runtime_overrides_model_and_temperature(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setenv("NOVEL_MODEL", "gpt-4.1-mini-env")
    monkeypatch.setenv("NOVEL_TEMPERATURE", "0.1")
    captured: dict[str, object] = {}

    def fake_call_api_stream(**kwargs):
        captured["model"] = kwargs["model"]
        captured["temperature"] = kwargs["temperature"]
        yield "output"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

    exit_code = main(
        [
            "polish",
            "chapters/001.md",
            "--model",
            "gpt-4.1-cli",
            "--temperature",
            "0.9",
        ]
    )

    assert exit_code == 0
    assert captured == {
        "model": "gpt-4.1-cli",
        "temperature": 0.9,
    }


def test_project_flag_uses_explicit_project_root(sample_project, workspace_dir, monkeypatch) -> None:
    outside_dir = workspace_dir / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "project flag output")
    monkeypatch.setattr(
        "novel_cli.cli.call_api_stream",
        lambda **_kwargs: iter(["project flag output"]),
    )

    exit_code = main(
        [
            "polish",
            "chapters/001.md",
            "--project",
            str(sample_project),
        ]
    )

    assert exit_code == 0
    assert (sample_project / "drafts" / "001.polished.md").read_text(encoding="utf-8") == "project flag output"


def test_prompt_flag_uses_explicit_template(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    prompt_path = sample_project / "custom.md"
    prompt_path.write_text("CUSTOM {{INSTRUCTION}} {{CHAPTER_TEXT}}", encoding="utf-8")
    captured: dict[str, str] = {}

    def fake_call_api_stream(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        yield "output"

    monkeypatch.setattr("novel_cli.cli.call_api_stream", fake_call_api_stream)

    exit_code = main(
        [
            "polish",
            "chapters/001.md",
            "--instruction",
            "保持克制",
            "--prompt",
            "custom.md",
        ]
    )

    assert exit_code == 0
    assert captured["prompt"] == "CUSTOM 保持克制 第一章的正文内容。"


def test_dry_run_prints_prompt_without_calling_api(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)

    def fail_call(**_kwargs):
        raise AssertionError("API should not be called during dry-run")

    monkeypatch.setattr("novel_cli.cli.call_api", fail_call)
    monkeypatch.setattr("novel_cli.cli.call_api_stream", fail_call)

    exit_code = main(["polish", "chapters/001.md", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# 润色任务" in captured.out
    assert not (sample_project / "drafts" / "001.polished.md").exists()


def test_dry_run_writes_prompt_to_custom_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)

    def fail_call(**_kwargs):
        raise AssertionError("API should not be called during dry-run")

    monkeypatch.setattr("novel_cli.cli.call_api", fail_call)
    monkeypatch.setattr("novel_cli.cli.call_api_stream", fail_call)

    exit_code = main(
        [
            "polish",
            "chapters/001.md",
            "--dry-run",
            "--out",
            "drafts/prompt-preview.md",
        ]
    )

    assert exit_code == 0
    prompt_output = sample_project / "drafts" / "prompt-preview.md"
    assert prompt_output.exists()
    assert "# 润色任务" in prompt_output.read_text(encoding="utf-8")


def test_json_output_returns_payload_and_disables_streaming(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    call_api_called: list[bool] = []

    def fake_call_api(**_kwargs):
        call_api_called.append(True)
        return "json output"

    def fail_stream(**_kwargs):
        raise AssertionError("streaming should be disabled for --json")

    monkeypatch.setattr("novel_cli.cli.call_api", fake_call_api)
    monkeypatch.setattr("novel_cli.cli.call_api_stream", fail_stream)

    exit_code = main(["polish", "chapters/001.md", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert call_api_called == [True]
    assert captured.err == ""
    assert payload["status"] == "ok"
    assert payload["mode"] == "polish"
    assert payload["output"].endswith("drafts\\001.polished.md") or payload["output"].endswith("drafts/001.polished.md")


def test_overwrite_flag_overwrites_existing_output(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    output = sample_project / "drafts" / "001.polished.md"
    output.write_text("old", encoding="utf-8")
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "new")
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["new"]))

    exit_code = main(["polish", "chapters/001.md", "--overwrite"])

    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == "new"
    assert not (sample_project / "drafts" / "001.polished.v2.md").exists()


def test_custom_out_path_versions_when_target_exists(sample_project, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    output = sample_project / "drafts" / "custom.md"
    output.write_text("old", encoding="utf-8")
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "new")
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["new"]))

    exit_code = main(["polish", "chapters/001.md", "--out", "drafts/custom.md"])

    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == "old"
    assert (sample_project / "drafts" / "custom.v2.md").read_text(encoding="utf-8") == "new"


def test_out_flag_rejects_writing_into_chapters(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setattr("novel_cli.cli.call_api", lambda **_kwargs: "unused")
    monkeypatch.setattr("novel_cli.cli.call_api_stream", lambda **_kwargs: iter(["unused"]))

    exit_code = main(["polish", "chapters/001.md", "--out", "chapters/001.polished.md"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Refusing to write output inside chapters" in captured.err


def test_context_command_outputs_json_preview(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)

    exit_code = main(["context", "chapters/001.md", "--mode", "polish", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert payload["status"] == "ok"
    assert payload["mode"] == "polish"
    assert payload["prompt_length"] > 0
    assert payload["output_preview"].endswith("drafts\\001.polished.md") or payload["output_preview"].endswith("drafts/001.polished.md")


def test_config_doctor_reports_blocking_issues_and_warnings(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    (sample_project / "docs" / "worldbuilding.md").unlink()

    exit_code = main(["config", "doctor", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert any("NOVEL_API_KEY" in issue for issue in payload["blocking_issues"])
    assert any("worldbuilding" in warning for warning in payload["warnings"])


def test_config_doctor_succeeds_when_environment_is_ready(sample_project, monkeypatch, capsys) -> None:
    monkeypatch.chdir(sample_project)
    monkeypatch.setenv("NOVEL_API_KEY", "test-key")

    exit_code = main(["config", "doctor", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["blocking_issues"] == []
