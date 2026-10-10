"""Shared publication identity and bounded filesystem destinations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

from .documents import DocumentError, load_mapping

REPO_ROOT = Path(__file__).resolve().parents[1]


class SiteConfigError(ValueError):
    """Invalid site configuration or an unsafe destination."""


def validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SiteConfigError("Use a nonempty lowercase hyphenated slug.")
    return slug


def safe_target(root: Path, relative_path: str) -> Path:
    relative = PurePosixPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or "\x00" in relative_path
        or relative.is_absolute()
        or any(part in {".", ".."} for part in relative_path.split("/"))
    ):
        raise SiteConfigError("Unsafe relative path.")
    if root.is_symlink():
        raise SiteConfigError("Refusing a symlinked destination root.")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise SiteConfigError("Refusing a symlinked destination.")
    if not current.resolve().is_relative_to(root.resolve()):
        raise SiteConfigError("Destination escapes its root.")
    return current


@dataclass(frozen=True)
class SiteConfig:
    root: Path
    docs_dir: Path
    output_dir: Path
    site_url: str
    quarto_version: str
    authors: dict[str, dict[str, str]]

    def published_url(self, relative_path: str) -> str:
        if (
            not isinstance(relative_path, str)
            or any(c in relative_path for c in "%?#:\\")
            or any(ord(c) < 32 for c in relative_path)
        ):
            raise SiteConfigError("Expected a relative publication path, not a URL.")
        safe_target(self.docs_dir, relative_path)
        return self.site_url + quote(relative_path, safe="/-._~")


def load_site_config(root: Path | None = None) -> SiteConfig:
    root = (root or REPO_ROOT).resolve()
    docs = safe_target(root, "docs")
    output = safe_target(root, "docs/_site")
    try:
        settings = load_mapping(safe_target(root, "docs/_quarto.yml").read_text(encoding="utf-8"))
        authors = load_mapping(
            safe_target(root, "config/authors.yml").read_text(encoding="utf-8")
        ).get("authors", {})
        version = safe_target(root, ".quarto-version").read_text(encoding="utf-8").strip()
    except (OSError, DocumentError) as exc:
        raise SiteConfigError(f"Cannot read site configuration ({type(exc).__name__}).") from None
    project = settings.get("project", {})
    website = settings.get("website", {})
    if not isinstance(project, dict) or not isinstance(website, dict):
        raise SiteConfigError("Project and website settings must be mappings.")
    if project.get("type") != "website" or project.get("output-dir") != "_site":
        raise SiteConfigError("Use a website project with output-dir: _site.")
    url = website.get("site-url", "")
    if not isinstance(url, str) or any(c.isspace() for c in url):
        raise SiteConfigError("Invalid publication URL.")
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and not any(part in {".", ".."} for part in parsed.path.split("/"))
            and "%" not in parsed.path
            and "\\" not in parsed.path
        )
        _ = parsed.port  # Validate malformed/non-numeric ports without echoing the URL.
    except ValueError:
        valid = False
    if not valid:
        raise SiteConfigError(
            "Use a public HTTPS site URL without credentials, query, or fragment."
        )
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SiteConfigError("Pin Quarto using a three-component version.")
    if not isinstance(authors, dict) or not authors:
        raise SiteConfigError("Register at least one author.")
    for author_id, record in authors.items():
        validate_slug(author_id)
        if not isinstance(record, dict) or not isinstance(record.get("name"), str):
            raise SiteConfigError("Each author requires a display name.")
        if not record["name"].strip():
            raise SiteConfigError("Author names must not be empty.")
    return SiteConfig(root, docs, output, url.rstrip("/") + "/", version, authors)
