from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .api_client import call_api, call_api_stream
from .config import RuntimeConfigOverrides, init_user_config, load_project_config
from .context_loader import GenerationContext, load_generation_context
from .errors import NovelCliError
from .file_utils import determine_output_path, resolve_path_from_project_root, write_output_file
from .output import (
    print_context_summary,
    print_doctor_summary,
    print_error,
    print_generation_summary,
    print_init_summary,
    print_json_payload,
    print_step,
    print_user_config_init_summary,
    set_verbose,
)
from .project_detector import resolve_project_root
from .project_initializer import init_project
from .prompt_builder import PromptBuildResult, build_prompt, load_prompt_template

GENERATION_HELP = {
    "polish": "Polish an existing chapter.",
    "continue": "Continue writing from the end of a chapter.",
    "rewrite": "Rewrite a chapter under a targeted instruction.",
    "summarize": "Summarize a chapter into structured notes.",
    "fill": "Fill content between two paragraphs marked with <!-- GAP -->.",
}
GENERATION_MODES = tuple(GENERATION_HELP.keys())


@dataclass(slots=True)
class PreparedGeneration:
    context: GenerationContext
    prompt_result: PromptBuildResult
    output_path: Path
    default_output_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novel",
        description="Global CLI for Chinese fiction workflows backed by an OpenAI-compatible API.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress step-by-step progress output.",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        default=False,
        help="Disable streaming output. Wait for the full response before printing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize a novel project in the current directory.")
    subparsers.add_parser("init-config", help="Initialize the user-level CLI config file.")

    for mode, help_text in GENERATION_HELP.items():
        command = subparsers.add_parser(mode, help=help_text)
        command.add_argument("chapter_file", help="Chapter path relative to the project root.")
        _add_generation_options(command)

    context_parser = subparsers.add_parser("context", help="Preview context, template, and output selection.")
    context_parser.add_argument("chapter_file", help="Chapter path relative to the project root.")
    context_parser.add_argument(
        "--mode",
        choices=GENERATION_MODES,
        required=True,
        help="Generation mode to preview.",
    )
    _add_generation_options(context_parser, include_output=False, include_dry_run=False)

    config_parser = subparsers.add_parser("config", help="Inspect CLI and project configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    doctor_parser = config_subparsers.add_parser("doctor", help="Check project and environment readiness.")
    doctor_parser.add_argument(
        "--project",
        help="Explicit project root directory. Defaults to auto-detection from the current working directory.",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON output.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    json_output = bool(getattr(args, "json", False))

    set_verbose(not args.quiet and not json_output)

    try:
        if args.command == "init":
            return _run_init()
        if args.command == "init-config":
            return _run_init_config()
        if args.command == "context":
            return _run_context(args)
        if args.command == "config" and args.config_command == "doctor":
            return _run_config_doctor(args)
        return _run_generation(
            args.command,
            args.chapter_file,
            args=args,
            stream=not args.no_stream and not json_output,
        )
    except NovelCliError as exc:
        if json_output:
            print_json_payload(
                {
                    "status": "error",
                    "error": exc.message,
                    "hint": exc.hint,
                }
            )
        else:
            print_error(exc)
        return 1


def _add_generation_options(
    parser: argparse.ArgumentParser,
    *,
    include_output: bool = True,
    include_dry_run: bool = True,
) -> None:
    parser.add_argument(
        "--project",
        help="Explicit project root directory. Defaults to auto-detection from the current working directory.",
    )
    parser.add_argument(
        "--instruction",
        default="",
        help="Extra instruction appended to the prompt.",
    )
    if include_output:
        parser.add_argument(
            "--out",
            help="Explicit output path. Relative paths are resolved from the project root.",
        )
    parser.add_argument(
        "--model",
        help="Override the configured model for this invocation only.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Override the configured temperature for this invocation only.",
    )
    parser.add_argument(
        "--prompt",
        help="Explicit prompt template path. Relative paths are resolved from the project root.",
    )
    if include_dry_run:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Build the final prompt without calling the API.",
        )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON output.",
    )
    if include_output:
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=None,
            help="Overwrite the target output path instead of versioning it.",
        )


def _run_init() -> int:
    result = init_project(Path.cwd())
    print_init_summary(result)
    return 0


def _run_init_config() -> int:
    result = init_user_config()
    print_user_config_init_summary(result)
    return 0


def _run_generation(
    mode: str,
    chapter_file: str,
    *,
    args: argparse.Namespace,
    stream: bool,
) -> int:
    prepared = _prepare_generation(
        mode,
        chapter_file,
        project_arg=args.project,
        instruction=args.instruction,
        out=args.out,
        model=args.model,
        temperature=args.temperature,
        prompt=args.prompt,
        overwrite=args.overwrite,
    )

    _print_preparation_steps(prepared)

    if args.dry_run:
        return _run_dry_run(prepared, args=args)

    generated_text = _call_generation_api(prepared, stream=stream)

    if mode == "fill":
        fill_len = len(generated_text)
        generated_text = (
            prepared.context.before_gap
            + "\n\n"
            + generated_text
            + "\n\n"
            + prepared.context.after_gap
        )
        print_step(
            f"[步骤 6/7] 组装并写入文件: {prepared.output_path} "
            f"(前段 {len(prepared.context.before_gap)} 字符 + 生成 {fill_len} 字符 + 后段 {len(prepared.context.after_gap)} 字符)"
        )
    else:
        print_step(f"[步骤 6/7] 写入文件: {prepared.output_path} ({len(generated_text)} 字符)")

    write_output_file(prepared.output_path, generated_text)

    if args.json:
        print_json_payload(
            _generation_payload(
                prepared,
                output_path=prepared.output_path,
                dry_run=False,
            )
        )
        return 0

    print_generation_summary(
        mode=mode,
        project_root=prepared.context.config.project_root,
        input_path=prepared.context.chapter_path,
        output_path=prepared.output_path,
        template_source=prepared.prompt_result.template_source,
        warnings=prepared.context.warnings,
    )
    return 0


def _run_dry_run(prepared: PreparedGeneration, *, args: argparse.Namespace) -> int:
    prompt_text = prepared.prompt_result.prompt
    actual_output_path: Path | None = None

    if args.out:
        actual_output_path = prepared.output_path
        print_step(f"[步骤 4/4] 写入 dry-run prompt: {actual_output_path} ({len(prompt_text)} 字符)")
        write_output_file(actual_output_path, prompt_text)
    else:
        print_step(f"[步骤 4/4] 输出 dry-run prompt: stdout ({len(prompt_text)} 字符)")

    if args.json:
        print_json_payload(
            _generation_payload(
                prepared,
                output_path=actual_output_path,
                dry_run=True,
                prompt=prompt_text,
            )
        )
        return 0

    if actual_output_path is not None:
        print(f"Dry-run prompt written to: {actual_output_path}")
    else:
        print(prompt_text)
    return 0


def _run_context(args: argparse.Namespace) -> int:
    prepared = _prepare_generation(
        args.mode,
        args.chapter_file,
        project_arg=args.project,
        instruction=args.instruction,
        out=None,
        model=args.model,
        temperature=args.temperature,
        prompt=args.prompt,
        overwrite=None,
    )

    print_step(f"[步骤 1/4] 检测项目: 项目根目录 {prepared.context.config.project_root}")
    _print_context_loading_details(prepared.context, step_label="[步骤 2/4] 加载上下文")
    print_step(
        f"[步骤 3/4] 构建提示词: 模板 {prepared.prompt_result.template_source}, "
        f"提示词长度 {len(prepared.prompt_result.prompt)} 字符"
    )
    print_step(f"[步骤 4/4] 预览输出路径: {prepared.default_output_path}")

    loaded_context = sum(1 for value in prepared.context.sections.values() if value)
    total_context = len(prepared.context.sections)
    payload = {
        "status": "ok",
        "mode": prepared.context.mode,
        "project_root": str(prepared.context.config.project_root),
        "input": str(prepared.context.chapter_path),
        "template": prepared.prompt_result.template_source,
        "output_preview": str(prepared.default_output_path),
        "model": prepared.context.config.model.name,
        "temperature": prepared.context.config.model.temperature,
        "base_url": prepared.context.config.api.base_url,
        "prompt_length": len(prepared.prompt_result.prompt),
        "loaded_context": loaded_context,
        "total_context": total_context,
        "warnings": prepared.context.warnings,
    }

    if args.json:
        print_json_payload(payload)
        return 0

    print_context_summary(
        mode=prepared.context.mode,
        project_root=prepared.context.config.project_root,
        input_path=prepared.context.chapter_path,
        template_source=prepared.prompt_result.template_source,
        output_path=prepared.default_output_path,
        model=prepared.context.config.model.name,
        temperature=prepared.context.config.model.temperature,
        base_url=prepared.context.config.api.base_url,
        prompt_length=len(prepared.prompt_result.prompt),
        loaded_context=loaded_context,
        total_context=total_context,
        warnings=prepared.context.warnings,
    )
    return 0


def _run_config_doctor(args: argparse.Namespace) -> int:
    blocking_issues: list[str] = []
    warnings: list[str] = []
    project_root: Path | None = None

    try:
        project_root = resolve_project_root(args.project, start_path=Path.cwd())
    except NovelCliError as exc:
        blocking_issues.append(_format_issue(exc))
        return _emit_doctor_result(
            project_root=project_root,
            blocking_issues=blocking_issues,
            warnings=warnings,
            json_output=args.json,
        )

    try:
        config = load_project_config(project_root)
    except NovelCliError as exc:
        blocking_issues.append(_format_issue(exc))
        return _emit_doctor_result(
            project_root=project_root,
            blocking_issues=blocking_issues,
            warnings=warnings,
            json_output=args.json,
        )

    novel_yaml = project_root / "novel.yaml"
    if not novel_yaml.exists():
        warnings.append(f"Project config file not found: {novel_yaml} (using defaults)")

    for directory in (config.paths.chapters, config.paths.drafts, config.paths.summaries):
        if not directory.is_dir():
            blocking_issues.append(f"Required directory not found: {directory}")

    if not os.getenv("NOVEL_API_KEY"):
        blocking_issues.append(
            "Missing NOVEL_API_KEY. Set it in your environment or project .env file."
        )

    for mode in GENERATION_MODES:
        try:
            load_prompt_template(config, mode)
        except NovelCliError as exc:
            blocking_issues.append(_format_issue(exc))

    for path in (
        config.context.style,
        config.context.characters,
        config.context.worldbuilding,
        config.context.timeline,
        config.context.glossary,
        config.context.story_so_far,
    ):
        if not path.exists():
            warnings.append(f"Optional context file not found: {path}")

    return _emit_doctor_result(
        project_root=project_root,
        blocking_issues=blocking_issues,
        warnings=warnings,
        json_output=args.json,
    )


def _emit_doctor_result(
    *,
    project_root: Path | None,
    blocking_issues: list[str],
    warnings: list[str],
    json_output: bool,
) -> int:
    status = "ok" if not blocking_issues else "error"
    if json_output:
        print_json_payload(
            {
                "status": status,
                "project_root": str(project_root) if project_root is not None else None,
                "blocking_issues": blocking_issues,
                "warnings": warnings,
            }
        )
    else:
        print_doctor_summary(
            project_root=project_root,
            blocking_issues=blocking_issues,
            warnings=warnings,
        )
    return 0 if not blocking_issues else 1


def _prepare_generation(
    mode: str,
    chapter_file: str,
    *,
    project_arg: str | None,
    instruction: str,
    out: str | None,
    model: str | None,
    temperature: float | None,
    prompt: str | None,
    overwrite: bool | None,
) -> PreparedGeneration:
    project_root = resolve_project_root(project_arg, start_path=Path.cwd())
    normalized_instruction = instruction or ""
    if mode == "rewrite" and not normalized_instruction.strip():
        raise NovelCliError(
            "`novel rewrite` requires `--instruction`.",
            "Pass a non-empty rewrite instruction, for example `--instruction \"改成第一人称\"`.",
        )

    config = load_project_config(
        project_root,
        overrides=RuntimeConfigOverrides(
            model_name=model,
            temperature=temperature,
        ),
    )
    context = load_generation_context(
        project_root,
        chapter_file,
        mode,
        instruction=normalized_instruction,
        config=config,
    )
    explicit_template = (
        resolve_path_from_project_root(project_root, prompt)
        if prompt
        else None
    )
    prompt_result = build_prompt(context, template_path=explicit_template)
    default_output_path = determine_output_path(
        config,
        context.chapter_path,
        mode,
    )
    output_path = determine_output_path(
        config,
        context.chapter_path,
        mode,
        explicit_output_path=(
            resolve_path_from_project_root(project_root, out)
            if out
            else None
        ),
        overwrite=overwrite,
    )
    return PreparedGeneration(
        context=context,
        prompt_result=prompt_result,
        output_path=output_path,
        default_output_path=default_output_path,
    )


def _print_preparation_steps(prepared: PreparedGeneration) -> None:
    print_step(f"[步骤 1/7] 检测项目: 项目根目录 {prepared.context.config.project_root}")
    _print_context_loading_details(prepared.context, step_label="[步骤 2/7] 加载上下文")
    print_step(
        f"[步骤 3/7] 构建提示词: 模板 {prepared.prompt_result.template_source}, "
        f"提示词长度 {len(prepared.prompt_result.prompt)} 字符"
    )
    print_step(f"[步骤 4/7] 确定输出路径: {prepared.output_path}")


def _print_context_loading_details(context: GenerationContext, *, step_label: str) -> None:
    novel_yaml = context.config.project_root / "novel.yaml"
    print_step(f"{step_label}: 项目配置 {novel_yaml}")

    from .config import get_user_config_path

    user_cfg_path = get_user_config_path()
    if user_cfg_path.exists():
        print_step(f"  用户配置: {user_cfg_path} (已加载)")
    else:
        print_step(f"  用户配置: {user_cfg_path} (未找到，使用默认值)")

    env_file = context.config.project_root / ".env"
    if env_file.exists():
        print_step(f"  环境文件: {env_file} (已加载)")

    loaded = sum(1 for value in context.sections.values() if value)
    total = len(context.sections)
    print_step(f"  章节: {context.chapter_path}")
    print_step(f"  可选上下文: {loaded}/{total} 已加载")
    for warning in context.warnings:
        print_step(f"  缺失: {warning}")
    if context.instruction.strip():
        print_step(f"  额外指令: {context.instruction.strip()}")

    print_step(
        f"  模型: {context.config.model.name}, "
        f"Base URL: {context.config.api.base_url}, "
        f"温度: {context.config.model.temperature}"
    )


def _call_generation_api(prepared: PreparedGeneration, *, stream: bool) -> str:
    if stream:
        print_step(
            f"[步骤 5/7] 调用 API (流式): 模型 {prepared.context.config.model.name}, "
            f"Base URL {prepared.context.config.api.base_url}, "
            f"温度 {prepared.context.config.model.temperature}, "
            f"提示词 {len(prepared.prompt_result.prompt)} 字符"
        )
        generated_text_parts: list[str] = []
        try:
            for token in call_api_stream(
                prompt=prepared.prompt_result.prompt,
                base_url=prepared.context.config.api.base_url,
                model=prepared.context.config.model.name,
                temperature=prepared.context.config.model.temperature,
            ):
                print(token, end="", flush=True)
                generated_text_parts.append(token)
        except Exception:
            print()
            raise
        print()
        generated_text = "".join(generated_text_parts)
        print_step(f"[步骤 5/7] API 调用完成: 响应长度 {len(generated_text)} 字符")
        return generated_text

    print_step(
        f"[步骤 5/7] 调用 API: 模型 {prepared.context.config.model.name}, "
        f"Base URL {prepared.context.config.api.base_url}, "
        f"温度 {prepared.context.config.model.temperature}, "
        f"提示词 {len(prepared.prompt_result.prompt)} 字符, 请等待..."
    )
    generated_text = call_api(
        prompt=prepared.prompt_result.prompt,
        base_url=prepared.context.config.api.base_url,
        model=prepared.context.config.model.name,
        temperature=prepared.context.config.model.temperature,
    )
    print_step(f"[步骤 5/7] API 调用完成: 响应长度 {len(generated_text)} 字符")
    return generated_text


def _generation_payload(
    prepared: PreparedGeneration,
    *,
    output_path: Path | None,
    dry_run: bool,
    prompt: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "ok",
        "mode": prepared.context.mode,
        "project_root": str(prepared.context.config.project_root),
        "input": str(prepared.context.chapter_path),
        "template": prepared.prompt_result.template_source,
        "model": prepared.context.config.model.name,
        "temperature": prepared.context.config.model.temperature,
        "base_url": prepared.context.config.api.base_url,
        "warnings": prepared.context.warnings,
        "dry_run": dry_run,
    }
    if output_path is not None:
        payload["output"] = str(output_path)
    if prepared.default_output_path != output_path:
        payload["output_preview"] = str(prepared.default_output_path)
    if prompt is not None:
        payload["prompt"] = prompt
    return payload


def _format_issue(error: NovelCliError) -> str:
    if error.hint:
        return f"{error.message} Hint: {error.hint}"
    return error.message
