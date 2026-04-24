from __future__ import annotations

import pytest

from novel_cli.config import load_project_config
from novel_cli.errors import NovelCliError
from novel_cli.file_utils import determine_output_path, next_available_path
from novel_cli.project_initializer import init_project


def test_next_available_path_increments_versions(workspace_dir) -> None:
    drafts_dir = workspace_dir / "drafts"
    drafts_dir.mkdir()
    (drafts_dir / "001.polished.md").write_text("v1", encoding="utf-8")
    (drafts_dir / "001.polished.v2.md").write_text("v2", encoding="utf-8")

    assert next_available_path(drafts_dir / "001.polished.md").name == "001.polished.v3.md"


def test_determine_output_path_rejects_chapters_directory(workspace_dir) -> None:
    init_project(workspace_dir)
    chapter_path = workspace_dir / "chapters" / "001.md"
    chapter_path.write_text("正文", encoding="utf-8")
    config = load_project_config(workspace_dir)

    with pytest.raises(NovelCliError, match="Refusing to write output inside chapters"):
        determine_output_path(
            config,
            chapter_path,
            "polish",
            explicit_output_path=workspace_dir / "chapters" / "001.polished.md",
        )
