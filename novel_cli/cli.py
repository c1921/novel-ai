from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .api_client import call_api
from .config import init_user_config
from .context_loader import load_generation_context
from .errors import NovelCliError
from .file_utils import determine_output_path, write_output_file
from .output import (
    print_error,
    print_generation_summary,
    print_init_summary,
    print_step,
    print_user_config_init_summary,
    set_verbose,
)
from .project_detector import detect_project_root
from .project_initializer import init_project
from .prompt_builder import build_prompt

GENERATION_HELP = {
    "polish": "Polish an existing chapter.",
    "continue": "Continue writing from the end of a chapter.",
    "summarize": "Summarize a chapter into structured notes.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novel",
        description="Global CLI for Chinese fiction workflows backed by an OpenAI-compatible API.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        help="Suppress step-by-step progress output.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize a novel project in the current directory.")
    subparsers.add_parser("init-config", help="Initialize the user-level CLI config file.")

    for mode, help_text in GENERATION_HELP.items():
        command = subparsers.add_parser(mode, help=help_text)
        command.add_argument("chapter_file", help="Chapter path relative to the project root.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    set_verbose(not args.quiet)

    try:
        if args.command == "init":
            return _run_init()
        if args.command == "init-config":
            return _run_init_config()
        return _run_generation(args.command, args.chapter_file)
    except NovelCliError as exc:
        print_error(exc)
        return 1


def _run_init() -> int:
    result = init_project(Path.cwd())
    print_init_summary(result)
    return 0


def _run_init_config() -> int:
    result = init_user_config()
    print_user_config_init_summary(result)
    return 0


def _run_generation(mode: str, chapter_file: str) -> int:
    # Step 1: Detect project root
    project_root = detect_project_root(Path.cwd())
    print_step(f"[步骤 1/7] 检测项目: 项目根目录 {project_root}")

    # Step 2: Load context
    context = load_generation_context(project_root, chapter_file, mode)

    novel_yaml = project_root / "novel.yaml"
    print_step(f"[步骤 2/7] 加载上下文: 项目配置 {novel_yaml}")

    from .config import get_user_config_path
    user_cfg_path = get_user_config_path()
    if user_cfg_path.exists():
        print_step(f"  用户配置: {user_cfg_path} (已加载)")
    else:
        print_step(f"  用户配置: {user_cfg_path} (未找到，使用默认值)")

    env_file = project_root / ".env"
    if env_file.exists():
        print_step(f"  环境文件: {env_file} (已加载)")

    loaded = sum(1 for v in context.sections.values() if v)
    total = len(context.sections)
    print_step(f"  章节: {context.chapter_path}")
    print_step(f"  可选上下文: {loaded}/{total} 已加载")
    for w in context.warnings:
        print_step(f"  缺失: {w}")

    print_step(
        f"  模型: {context.config.model.name}, "
        f"Base URL: {context.config.api.base_url}, "
        f"温度: {context.config.model.temperature}"
    )

    # Step 3: Build prompt
    prompt_result = build_prompt(context)
    print_step(
        f"[步骤 3/7] 构建提示词: 模板 {prompt_result.template_source}, "
        f"提示词长度 {len(prompt_result.prompt)} 字符"
    )

    # Step 4: Determine output path
    output_path = determine_output_path(context.config, context.chapter_path, mode)
    print_step(f"[步骤 4/7] 确定输出路径: {output_path}")

    # Step 5: Call API
    print_step(
        f"[步骤 5/7] 调用 API: 模型 {context.config.model.name}, "
        f"Base URL {context.config.api.base_url}, "
        f"温度 {context.config.model.temperature}, "
        f"提示词 {len(prompt_result.prompt)} 字符, 请等待..."
    )
    generated_text = call_api(
        prompt=prompt_result.prompt,
        base_url=context.config.api.base_url,
        model=context.config.model.name,
        temperature=context.config.model.temperature,
    )
    print_step(f"[步骤 5/7] API 调用完成: 响应长度 {len(generated_text)} 字符")

    # Step 6: Write output
    write_output_file(output_path, generated_text)
    print_step(f"[步骤 6/7] 写入文件: {output_path} ({len(generated_text)} 字符)")

    # Step 7: Summary (always prints to stdout)
    print_generation_summary(
        mode=mode,
        project_root=context.config.project_root,
        input_path=context.chapter_path,
        output_path=output_path,
        template_source=prompt_result.template_source,
        warnings=context.warnings,
    )
    return 0
