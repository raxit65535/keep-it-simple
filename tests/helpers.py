"""Small filesystem fixtures; never copy real personal notes into tests."""

from pathlib import Path

import yaml


def make_site_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "docs").mkdir(parents=True)
    (root / "config").mkdir()
    config = {
        "project": {"type": "website", "output-dir": "_site"},
        "website": {"site-url": "https://example.test/keep-it-simple/"},
        "execute": {"enabled": False},
    }
    (root / "docs/_quarto.yml").write_text(yaml.safe_dump(config), encoding="utf-8")
    (root / "config/authors.yml").write_text(
        yaml.safe_dump({"authors": {"raxit": {"name": "Raxit Solanki"}}}), encoding="utf-8"
    )
    (root / ".quarto-version").write_text("1.10.19\n", encoding="utf-8")
    (root / "config/redirects.yml").write_text("redirects: {}\n", encoding="utf-8")
    (root / "docs/.nojekyll").touch()
    return root
