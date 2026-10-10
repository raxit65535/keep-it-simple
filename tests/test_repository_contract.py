"""Single publishing stack and core-only CLI availability."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_obsolete_active_tooling_is_removed():
    for path in (
        "mkdocs.yml",
        ".mise.toml",
        "requirements.txt",
        "hooks/socialmedia.py",
        "scripts/mkdocs_hooks.py",
        "overrides/home.html",
        "overrides/css/extra.css",
    ):
        assert not (ROOT / path).exists()


def test_core_cli_help_does_not_require_running_agents_or_renderer():
    for module in ("tools.new_post", "tools.build_site", "research_agent"):
        result = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Usage" in result.stdout or "usage" in result.stdout
