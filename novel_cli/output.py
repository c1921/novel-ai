from __future__ import annotations

import json
from pathlib import Path
import sys

_verbose = True


def set_verbose(enabled: bool) -> None:
    """Enable or disable verbose step-by-step output to stderr."""
    global _verbose
    _verbose = enabled


def print_step(message: str) -> None:
    """Print a step progress line to stderr when verbose mode is active."""
    if _verbose:
        print(message, file=sys.stderr)


from .errors import NovelCliError
from .config import UserConfigInitResult
from .project_initializer import InitResult


def print_init_summary(result: InitResult) -> None:
    print(f"Initialized project at {result.project_root}")
    for path in result.created:
        print(f"Created: {path}")
    for path in result.skipped:
        print(f"Skipped existing: {path}")


def print_user_config_init_summary(result: UserConfigInitResult) -> None:
    if result.created:
        print(f"Created user config: {result.config_path}")
    else:
        print(f"Skipped existing user config: {result.config_path}")


def print_generation_summary(
    *,
    mode: str,
    project_root: Path,
    input_path: Path,
    output_path: Path,
    template_source: str,
    warnings: list[str],
) -> None:
    for warning in warnings:
        print_warning(warning)

    print(f"Mode: {mode}")
    print(f"Project root: {project_root}")
    print(f"Input: {input_path}")
    print(f"Template: {template_source}")
    print(f"Output: {output_path}")


def print_context_summary(
    *,
    mode: str,
    project_root: Path,
    input_path: Path,
    template_source: str,
    output_path: Path,
    model: str,
    temperature: float,
    base_url: str,
    prompt_length: int,
    loaded_context: int,
    total_context: int,
    warnings: list[str],
) -> None:
    print(f"Mode: {mode}")
    print(f"Project root: {project_root}")
    print(f"Input: {input_path}")
    print(f"Template: {template_source}")
    print(f"Output: {output_path}")
    print(f"Model: {model}")
    print(f"Temperature: {temperature}")
    print(f"Base URL: {base_url}")
    print(f"Loaded context: {loaded_context}/{total_context}")
    print(f"Estimated prompt length: {prompt_length}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


def print_doctor_summary(
    *,
    project_root: Path | None,
    blocking_issues: list[str],
    warnings: list[str],
) -> None:
    status = "ok" if not blocking_issues else "error"
    print(f"Status: {status}")
    if project_root is not None:
        print(f"Project root: {project_root}")
    print("Blocking issues:")
    if blocking_issues:
        for issue in blocking_issues:
            print(f"- {issue}")
    else:
        print("- none")

    print("Warnings:")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- none")


def print_json_payload(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_warning(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def print_error(error: NovelCliError) -> None:
    print(f"Error: {error.message}", file=sys.stderr)
    if error.hint:
        print(f"Hint: {error.hint}", file=sys.stderr)
