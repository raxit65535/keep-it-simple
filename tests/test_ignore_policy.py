"""Check actual Git ignore behavior without the developer's global exclusions."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_repository(tmp_path):
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    subprocess.run(
        ["git", "-c", "init.defaultBranch=main", "init", "--quiet", "--template=", str(tmp_path)],
        env=env,
        check=True,
        capture_output=True,
    )
    shutil.copy2(ROOT / ".gitignore", tmp_path / ".gitignore")
    return tmp_path, env


def ignored_paths(repository, paths):
    root, env = repository
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=root,
        env=env,
        input="\n".join(paths) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode in {0, 1}, result.stderr
    return set(result.stdout.splitlines())


def test_private_local_files_stay_out_of_git(isolated_repository):
    paths = {
        ".personal/synthetic-note.md",
        ".agent/plans/local-only.md",
        ".superpowers/brainstorm/session/state/server-info",
        ".local/quarto/bin/quarto",
        "drafts/synthetic-run/index.qmd",
        "docs/_site/index.html",
        "docs/.quarto/cache.json",
        ".idea/modules.xml",
        ".vscode/settings.json",
        ".env",
        ".env.local",
        ".env.production",
        "tools/.env.development",
        "keys/server.pem",
        "keys/server.key",
        "keys/client.p12",
        "keys/client.pfx",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "application_default_credentials.json",
        "service-account-test.json",
        "secrets.yml",
    }
    assert ignored_paths(isolated_repository, paths) == paths


def test_portable_sources_and_safe_env_templates_remain_visible(isolated_repository):
    paths = {
        "README.md",
        "AGENTS.md",
        "HANDOFF.md",
        ".gitignore",
        ".python-version",
        ".quarto-version",
        "pyproject.toml",
        "uv.lock",
        ".env.example",
        ".env.template",
        "docs/.nojekyll",
        "docs/_quarto.yml",
        "docs/assets/profile.jpg",
        "config/authors.yml",
        "tools/build_site.py",
        "research_agent/graph.py",
        "templates/project.qmd",
        "tests/test_validate_site.py",
        ".github/workflows/ci.yml",
    }
    assert ignored_paths(isolated_repository, paths) == set()
