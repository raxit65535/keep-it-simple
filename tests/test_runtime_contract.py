"""The default environment and ignore boundary must support safe authoring."""

import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_default_environment_can_use_framework_models_without_llm_dependencies():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    core = project["project"]["dependencies"]
    assert any(name.startswith("pydantic") for name in core)
    assert not any(name.startswith(("mkdocs", "langgraph", "langchain")) for name in core)
    agent = project["dependency-groups"]["agent"]
    assert any(name.startswith("langgraph") for name in agent)
    assert any(name.startswith("langchain-openai") for name in agent)
    assert any(name.startswith("langchain-ollama") for name in agent)


def test_generated_drafts_do_not_dirty_git():
    result = subprocess.run(
        ["git", "check-ignore", "drafts/synthetic-run/post/index.qmd"],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode == 0


def test_personal_notes_are_ignored_and_untracked():
    result = subprocess.run(
        ["git", "check-ignore", ".personal/synthetic.qmd"], cwd=ROOT, capture_output=True
    )
    assert result.returncode == 0
    assert subprocess.check_output(["git", "ls-files", "--", ".personal/"], cwd=ROOT) == b""
