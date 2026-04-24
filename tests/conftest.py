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
def sample_project(workspace_dir: Path) -> Path:
    init_project(workspace_dir)
    (workspace_dir / "chapters" / "001.md").write_text("第一章的正文内容。", encoding="utf-8")
    return workspace_dir
