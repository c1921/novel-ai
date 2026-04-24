from __future__ import annotations

from novel_cli.file_utils import next_available_path


def test_next_available_path_increments_versions(workspace_dir) -> None:
    drafts_dir = workspace_dir / "drafts"
    drafts_dir.mkdir()
    (drafts_dir / "001.polished.md").write_text("v1", encoding="utf-8")
    (drafts_dir / "001.polished.v2.md").write_text("v2", encoding="utf-8")

    assert next_available_path(drafts_dir / "001.polished.md").name == "001.polished.v3.md"
