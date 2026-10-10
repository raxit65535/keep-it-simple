"""Export autonomous research runs as explicit, unverified Quarto bundles."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

from tools.scaffold import PostSpec, ScaffoldError, create_post
from tools.site_config import SiteConfigError, load_site_config, safe_target

from .bibliography import write_bibliography, write_sources_yaml
from .models import Paper
from .social import generate_social_copy, write_social_copy

DISCLOSURE = """::: {.callout-note}
## Unverified literature draft

This draft was generated from retrieved abstracts and metadata. It is not a
full-text review or independently validated research. Verify the cited sources
and the claims they support before publication.
:::
"""


@dataclass(frozen=True)
class DraftBundle:
    post_dir: Path
    post_file: Path
    files: tuple[Path, ...]
    post_url: str


def write_draft_bundle(
    spec: PostSpec,
    papers: list[Paper],
    *,
    run_id: str,
    repo_root: Path | None = None,
) -> DraftBundle:
    config = load_site_config(repo_root)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", run_id):
        raise ScaffoldError("Run id must be a single safe directory name.")
    try:
        output = safe_target(config.root, f"drafts/{run_id}")
        target = safe_target(output, spec.slug)
    except SiteConfigError as exc:
        raise ScaffoldError(str(exc)) from None
    if target.exists():
        raise ScaffoldError("Draft bundle already exists; start a new run.")
    draft = replace(
        spec,
        kind="paper-analysis",
        draft=True,
        bibliography=f"{spec.slug}.bib",
        body=DISCLOSURE + "\n" + spec.body,
    )
    result = create_post(draft, output_root=output, repo_root=config.root)
    bib = write_bibliography(papers, result.post_dir, spec.slug)
    sources = write_sources_yaml(papers, result.assets_dir)
    post_url = config.published_url(f"posts/{spec.slug}/")
    copy = generate_social_copy(spec.title, post_url, spec.description, spec.tags)
    social = write_social_copy(copy, result.assets_dir)
    return DraftBundle(
        result.post_dir, result.post_file, (result.post_file, bib, sources, social), post_url
    )
