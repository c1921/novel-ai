from __future__ import annotations

from pathlib import Path
import tomllib


def test_package_data_explicitly_includes_project_gitignore() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    package_data = pyproject["tool"]["setuptools"]["package-data"]["novel_cli"]

    assert "templates/project/.gitignore" in package_data


def test_runtime_docs_and_templates_use_openai_compatible_api_naming() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    user_template = (repo_root / "novel_cli" / "templates" / "config" / "config.yaml").read_text(encoding="utf-8")
    project_template = (repo_root / "novel_cli" / "templates" / "project" / "novel.yaml").read_text(encoding="utf-8")

    assert "OpenAI-compatible API" in pyproject
    assert "DEEPSEEK_" not in pyproject
    assert "DEEPSEEK_" not in readme
    assert "deepseek:" not in user_template
    assert "provider:" not in project_template
    assert "DEEPSEEK_" not in user_template
    assert "DEEPSEEK_" not in project_template


def test_api_client_module_replaces_deepseek_client_module() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    assert (repo_root / "novel_cli" / "api_client.py").exists()
    assert not (repo_root / "novel_cli" / "deepseek_client.py").exists()
