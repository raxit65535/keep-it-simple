"""Clean, non-executing Quarto render with publication checks; never deploys."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .documents import DocumentError
from .redirects import write_redirects
from .site_config import SiteConfig, SiteConfigError, load_site_config, safe_target
from .validate_site import ValidationError, validate_output, validate_sources


def clean_output(config: SiteConfig) -> None:
    expected = config.root / "docs/_site"
    try:
        safe_target(config.root, "docs/_site")
    except SiteConfigError as exc:
        raise ValidationError(str(exc)) from None
    if config.output_dir != expected or not expected.resolve().is_relative_to(config.docs_dir):
        raise ValidationError("Refusing to clean an unowned output directory.")
    if expected.exists():
        if not expected.is_dir():
            raise ValidationError("Output must be a directory.")
        shutil.rmtree(expected)
    expected.mkdir(parents=True)


def build_site(root: Path | None = None, quarto: str = "quarto") -> Path:
    config = load_site_config(root)
    problems = validate_sources(config)
    if problems:
        raise ValidationError("\n".join(problems))
    try:
        version = subprocess.run(
            [quarto, "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise ValidationError(
            f"Install Quarto {config.quarto_version} and put it on PATH."
        ) from None
    if version != config.quarto_version:
        raise ValidationError(f"Quarto {config.quarto_version} is required (found {version}).")
    clean_output(config)
    result = subprocess.run(
        [quarto, "render", str(config.docs_dir), "--no-execute", "--to", "html"],
        cwd=config.root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "NO_COLOR": "1"},
    )
    diagnostics = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout + "\n" + result.stderr)
    if result.returncode:
        raise ValidationError("Quarto rendering failed:\n" + diagnostics)
    if re.search(r"(?im)^\s*(?:\[(?:WARNING|WARN)\]|(?:WARNING|WARN)\b)", diagnostics):
        raise ValidationError("Quarto emitted a warning:\n" + diagnostics)
    write_redirects(config)
    problems = validate_output(config)
    if problems:
        raise ValidationError("\n".join(problems))
    return config.output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Repository root (defaults to this checkout)")
    parser.add_argument("--quarto", default="quarto", help="Path to the pinned Quarto executable")
    args = parser.parse_args()
    try:
        output = build_site(args.root, args.quarto)
    except (ValidationError, SiteConfigError, DocumentError, OSError) as exc:
        print(f"Build refused: {exc}", file=sys.stderr)
        return 1
    print(f"Validated public site: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
