"""Generate platform-specific social copy for a published post (manual posting)."""

from __future__ import annotations

from pathlib import Path

import yaml

MAX_X = 280


def _hashtags(tags: list[str]) -> str:
    return " ".join("#" + t.replace(" ", "") for t in tags[:4])


def generate_social_copy(
    title: str, url: str, summary: str, tags: list[str] | None = None
) -> dict[str, str]:
    """Return draft copy per platform. Nothing is posted automatically."""
    tags = tags or []
    hashtags = _hashtags(tags)

    x_body = f"{title}\n\n{summary.strip()}"
    budget = MAX_X - len(url) - len(hashtags) - 4
    if len(x_body) > budget:
        x_body = x_body[: max(0, budget - 1)].rstrip() + "…"
    x_post = f"{x_body}\n\n{url}\n{hashtags}".strip()

    linkedin = (
        f"{title}\n\n{summary.strip()}\n\n"
        f"Read the full write-up: {url}\n\n{hashtags}"
    ).strip()

    return {"x": x_post, "linkedin": linkedin}


def write_social_copy(copy: dict[str, str], assets_dir: Path) -> Path:
    """Persist the drafts beside the post for easy copy-paste."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    path = assets_dir / "social.yml"
    path.write_text(
        yaml.safe_dump(copy, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path
