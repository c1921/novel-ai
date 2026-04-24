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
    print_user_config_init_summary,
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
    project_root = detect_project_root(Path.cwd())
    context = load_generation_context(project_root, chapter_file, mode)
    prompt_result = build_prompt(context)
    output_path = determine_output_path(context.config, context.chapter_path, mode)
    generated_text = call_api(
        prompt=prompt_result.prompt,
        base_url=context.config.api.base_url,
        model=context.config.model.name,
        temperature=context.config.model.temperature,
    )
    write_output_file(output_path, generated_text)
    print_generation_summary(
        mode=mode,
        project_root=context.config.project_root,
        input_path=context.chapter_path,
        output_path=output_path,
        template_source=prompt_result.template_source,
        warnings=context.warnings,
    )
    return 0
