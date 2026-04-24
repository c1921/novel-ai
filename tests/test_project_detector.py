from __future__ import annotations

import pytest

from novel_cli.errors import NovelCliError
from novel_cli.project_detector import detect_project_root


def test_detect_project_root_from_nested_directory(workspace_dir) -> None:
    project_root = workspace_dir / "my-novel"
    nested_dir = project_root / "workspace" / "drafts"
    nested_dir.mkdir(parents=True)
    (project_root / "novel.yaml").write_text("project_name: my-novel\n", encoding="utf-8")

    assert detect_project_root(nested_dir) == project_root.resolve()


def test_detect_project_root_from_chapters_directory_fallback(workspace_dir) -> None:
    (workspace_dir / "chapters").mkdir()

    assert detect_project_root(workspace_dir) == workspace_dir.resolve()


def test_detect_project_root_failure(workspace_dir) -> None:
    with pytest.raises(NovelCliError, match="Could not locate a novel project root"):
        detect_project_root(workspace_dir)
