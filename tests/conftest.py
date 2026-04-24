from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from novel_cli.project_initializer import init_project

TEST_WORKSPACES = Path(__file__).resolve().parents[1] / ".test-workspaces"


@pytest.fixture
def workspace_dir() -> Path:
    TEST_WORKSPACES.mkdir(parents=True, exist_ok=True)
    path = TEST_WORKSPACES / f"case-{uuid.uuid4().hex}"
    path.mkdir()
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def user_config_file(workspace_dir: Path, monkeypatch) -> Path:
    path = workspace_dir / "user-config" / "config.yaml"
    monkeypatch.setattr("novel_cli.config.get_user_config_path", lambda: path)
    return path


@pytest.fixture(autouse=True)
def isolate_user_config(user_config_file: Path) -> None:
    return None


@pytest.fixture(autouse=True)
def reset_verbose() -> None:
    """Reset verbose flag before each test to avoid cross-test leaks."""
    from novel_cli.output import set_verbose
    set_verbose(True)


@pytest.fixture(autouse=True)
def isolate_novel_env(monkeypatch) -> None:
    for env_name in (
        "NOVEL_API_KEY",
        "NOVEL_BASE_URL",
        "NOVEL_MODEL",
        "NOVEL_TEMPERATURE",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL",
    ):
        monkeypatch.delenv(env_name, raising=False)


@pytest.fixture
def sample_project(workspace_dir: Path) -> Path:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("第一章的正文内容。", encoding="utf-8")
    return workspace_dir
