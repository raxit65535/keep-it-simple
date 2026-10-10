"""Shared Quarto draft scaffolding for interactive authors and research agents."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

from slugify import slugify

from .documents import render_document
from .site_config import REPO_ROOT, SiteConfigError, load_site_config, safe_target, validate_slug

POSTS_DIR = REPO_ROOT / "docs/posts"


class ScaffoldError(ValueError):
    """Invalid metadata, unsafe output, or an existing article."""


@dataclass
class PostSpec:
    title: str
    author: str
    description: str
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    date: dt.date = field(default_factory=dt.date.today)
    slug: str = ""
    body: str = ""
    kind: str = "post"
    draft: bool = True
    bibliography: str | None = None
    ai_assisted: bool = False

    def __post_init__(self):
        if not isinstance(self.title, str) or not self.title.strip():
            raise ScaffoldError("A nonempty title is required.")
        if not self.slug:
            self.slug = slugify(self.title)
        try:
            validate_slug(self.slug)
        except SiteConfigError as exc:
            raise ScaffoldError(str(exc)) from None


@dataclass
class ScaffoldResult:
    post_dir: Path
    post_file: Path
    img_dir: Path
    assets_dir: Path


def load_author_ids(repo_root: Path | None = None) -> list[str]:
    return list(load_site_config(repo_root).authors)


def render_post(spec: PostSpec, *, repo_root: Path | None = None) -> str:
    try:
        config = load_site_config(repo_root)
        validate_slug(spec.slug)
        if spec.author not in config.authors:
            raise ScaffoldError("Unknown author; register it in config/authors.yml.")
        if not isinstance(spec.description, str) or not isinstance(spec.body, str):
            raise ScaffoldError("Description and body must be text.")
        if not isinstance(spec.date, dt.date):
            raise ScaffoldError("Use a calendar date for the article.")
        if not isinstance(spec.draft, bool) or not isinstance(spec.ai_assisted, bool):
            raise ScaffoldError("Draft and AI-assistance flags must be booleans.")
        if not isinstance(spec.kind, str) or spec.kind not in {
            "post",
            "paper-analysis",
            "project",
            "publication",
            "talk",
        }:
            raise ScaffoldError("Unknown content kind.")
        for values in (spec.categories, spec.tags):
            if not isinstance(values, list) or any(
                not isinstance(v, str) or not v.strip() for v in values
            ):
                raise ScaffoldError("Categories and tags must be lists of nonempty strings.")
        if spec.bibliography is not None:
            if not isinstance(spec.bibliography, str) or not spec.bibliography.endswith(".bib"):
                raise ScaffoldError("Bibliography must name a local .bib file.")
            safe_target(config.root / "drafts", spec.bibliography)
    except SiteConfigError as exc:
        raise ScaffoldError(str(exc)) from None
    metadata = {
        "title": spec.title,
        "author": [{"name": config.authors[spec.author]["name"]}],
        "description": spec.description,
        "date": spec.date,
        "categories": list(dict.fromkeys([*spec.categories, *spec.tags])),
        "tags": spec.tags,
        "kind": spec.kind,
        "draft": spec.draft,
        "ai-assisted": spec.ai_assisted,
    }
    if spec.bibliography is not None:
        metadata["bibliography"] = spec.bibliography
    body = spec.body.strip() or (
        "## Context\n\nExplain the problem and intended reader.\n\n"
        "## Explanation\n\n## Example\n\n## Limitations\n\n## References\n"
    )
    return render_document(metadata, body)


def create_post(
    spec: PostSpec,
    *,
    overwrite: bool = False,
    output_root: Path | None = None,
    repo_root: Path | None = None,
) -> ScaffoldResult:
    """Write a draft bundle, never implicitly write into the public site."""
    text = render_post(spec, repo_root=repo_root)
    root = (repo_root or REPO_ROOT).resolve()
    base = output_root or root / "drafts"
    if not base.is_absolute():
        base = root / base
    try:
        if not base.is_relative_to(root / "drafts"):
            raise ScaffoldError("Draft output must remain under drafts/.")
        base = safe_target(root, base.relative_to(root).as_posix())
        directory = safe_target(base, spec.slug)
        post = safe_target(directory, "index.qmd")
        image_dir = safe_target(directory, "img")
        assets_dir = safe_target(directory, "assets")
        if post.exists() and not overwrite:
            raise ScaffoldError("Post already exists; overwrite requires an explicit request.")
        for path in (image_dir, assets_dir):
            if path.exists() and not path.is_dir():
                raise ScaffoldError("An asset directory is occupied by a file.")
        for path in (directory, image_dir, assets_dir):
            path.mkdir(parents=True, exist_ok=True)
        post.write_text(text, encoding="utf-8")
    except (SiteConfigError, OSError) as exc:
        raise ScaffoldError(f"Cannot scaffold draft: {exc}") from None
    return ScaffoldResult(directory, post, image_dir, assets_dir)
