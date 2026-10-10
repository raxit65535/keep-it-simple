"""Prepare a site change on a research branch and open a PR; never merge/deploy."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tools.documents import DocumentError, read_document, render_document
from tools.site_config import SiteConfigError, safe_target, validate_slug

from .config import REPO_ROOT


class PublishError(RuntimeError):
    """Publication refused or partially completed; user work is preserved."""


def _git(*args: str, root: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root or REPO_ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode:
        # Git remote errors can contain authenticated URLs; do not echo them.
        raise PublishError(
            f"git {args[0]} failed (exit {result.returncode}); inspect repository state."
        )
    return result.stdout.strip()


def _gh_available() -> bool:
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, check=False)
        return result.returncode == 0
    except OSError:
        return False


def _branch_exists(branch: str, *, root: Path | None = None) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root or REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise PublishError("Cannot inspect the target research branch.")
    return result.returncode == 0


def validate_bundle_paths(paths: list[Path], root: Path) -> Path:
    """Require a complete declared bundle; never recursively collect neighbor data."""
    root = root.resolve()
    if not paths or len(set(paths)) != len(paths):
        raise PublishError("Select a nonempty bundle without duplicate paths.")
    normalized = []
    try:
        for path in paths:
            path = path if path.is_absolute() else root / path
            relative = path.relative_to(root)
            if relative.parts[0] != "drafts" or any(
                part.startswith(".") for part in relative.parts
            ):
                raise PublishError(
                    "Only explicit, non-hidden files under drafts/ can be published."
                )
            checked = safe_target(root, relative.as_posix())
            if not checked.is_file():
                raise PublishError("Every declared bundle entry must be a regular file.")
            normalized.append(checked)
        if len(set(normalized)) != len(normalized):
            raise PublishError("Duplicate bundle paths.")
        posts = [p for p in normalized if p.name == "index.qmd"]
        if len(posts) != 1:
            raise PublishError("The bundle must contain exactly one index.qmd.")
        directory = posts[0].parent
        if any(not p.is_relative_to(directory) for p in normalized):
            raise PublishError("Selected files must belong to one bundle.")
        actual = set()
        for path in directory.rglob("*"):
            if path.is_symlink() or any(
                p.startswith(".") for p in path.relative_to(directory).parts
            ):
                raise PublishError(
                    "Hidden or symlinked files are not allowed in a publication bundle."
                )
            if path.is_file():
                actual.add(path)
        if actual != set(normalized):
            raise PublishError("Bundle contains undeclared files; review the exact file set.")
        metadata, _ = read_document(posts[0])
        if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
            raise PublishError("The article requires a title.")
        if not isinstance(metadata.get("draft"), bool):
            raise PublishError("The article requires an explicit boolean draft state.")
    except (ValueError, OSError, DocumentError) as exc:
        raise PublishError(f"Invalid publication bundle ({type(exc).__name__}).") from None
    return directory


def preflight_publication(root: Path, bundle_files: list[Path], destination: Path) -> str:
    root = root.resolve()
    try:
        slug = validate_slug(destination.name)
        expected = safe_target(root, f"docs/posts/{slug}")
        if destination != expected:
            raise PublishError("Publication must target docs/posts/<slug>/.")
        if destination.exists():
            raise PublishError("Destination already exists.")
        validate_bundle_paths(bundle_files, root)
    except SiteConfigError as exc:
        raise PublishError(str(exc)) from None
    if _git("status", "--porcelain", "--untracked-files=no", root=root):
        raise PublishError(
            "Commit or set aside unrelated tracked/staged changes before opening a PR."
        )
    allowed = {
        (p if p.is_absolute() else root / p).relative_to(root).as_posix() for p in bundle_files
    }
    untracked = set(
        filter(
            None, _git("ls-files", "--others", "--exclude-standard", "-z", root=root).split("\0")
        )
    )
    if not untracked.issubset(allowed):
        raise PublishError(
            "Unrelated untracked files exist; keep them out of automated publication."
        )
    base = _git("branch", "--show-current", root=root)
    if not base or base == "gh-pages":
        raise PublishError(
            "Start from a named source branch, not a deployment or detached checkout."
        )
    if _branch_exists(f"research/{slug}", root=root):
        raise PublishError("Research branch already exists; use a new slug or review that branch.")
    if not _gh_available():
        raise PublishError("Install and authenticate the GitHub CLI before creating a review PR.")
    auth = subprocess.run(
        ["gh", "auth", "status"], cwd=root, capture_output=True, text=True, check=False
    )
    if auth.returncode:
        raise PublishError("Authenticate the GitHub CLI before creating a review PR.")
    return base


def open_pull_request(*, slug: str, title: str, paths: list[Path], dry_run: bool) -> str | None:
    if dry_run:
        return None
    root = REPO_ROOT.resolve()
    try:
        validate_slug(slug)
        bundle = validate_bundle_paths(paths, root)
        destination = safe_target(root, f"docs/posts/{slug}")
        base = preflight_publication(root, paths, destination)
    except (SiteConfigError, OSError) as exc:
        raise PublishError(str(exc)) from None
    branch = f"research/{slug}"
    stage = "preflight"
    try:
        _git("checkout", "-b", branch, root=root)
        stage = "branch created"
        published = []
        for source in paths:
            source = source if source.is_absolute() else root / source
            source = safe_target(root, source.relative_to(root).as_posix())
            target = safe_target(destination, source.relative_to(bundle).as_posix())
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            published.append(target.relative_to(root).as_posix())
        metadata, body = read_document(destination / "index.qmd")
        metadata["draft"] = False  # Publication intent; evidence/AI status is unchanged.
        (destination / "index.qmd").write_text(render_document(metadata, body), encoding="utf-8")
        _git("add", "--", *published, root=root)
        _git(
            "commit",
            "--only",
            "-m",
            f"research: add literature review — {title}",
            "--",
            *published,
            root=root,
        )
        stage = "committed"
        _git("push", "-u", "origin", branch, root=root)
        stage = "pushed"
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base,
                "--head",
                branch,
                "--title",
                f"Research: {title}",
                "--body",
                "Automated, unverified literature draft based on "
                "retrieved abstracts and metadata.\n\n"
                "Review the Quarto article, bibliography, sources, and claims before merging. "
                "The PR contains the intended site page; no second promotion is required.",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or not result.stdout.strip().startswith("https://"):
            raise PublishError(
                "PR creation failed; open the review PR manually from the pushed branch."
            )
        return result.stdout.strip()
    except (PublishError, OSError, DocumentError) as exc:
        raise PublishError(
            f"Publication stopped ({stage}) on {branch}; files retained. {exc}"
        ) from None
