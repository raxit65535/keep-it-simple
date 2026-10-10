"""Static compatibility redirects; GitHub Pages does not implement _redirects."""

from html import escape
from pathlib import Path

from .documents import load_mapping
from .site_config import SiteConfig, SiteConfigError, safe_target


def write_redirects(config: SiteConfig) -> list[Path]:
    path = safe_target(config.root, "config/redirects.yml")
    mapping = load_mapping(path.read_text(encoding="utf-8")).get("redirects", {})
    if not isinstance(mapping, dict):
        raise SiteConfigError("Redirects must be a mapping.")
    pending: dict[Path, str] = {}
    for alias, target in mapping.items():
        url = config.published_url(target)
        config.published_url(alias)
        destination = safe_target(config.output_dir, alias.rstrip("/") + "/index.html")
        target_file = safe_target(config.output_dir, target.rstrip("/") + "/index.html")
        if destination == target_file or destination in pending:
            raise SiteConfigError("Ambiguous or circular redirect.")
        if destination.exists():
            raise SiteConfigError("Redirect would overwrite an existing page.")
        if not target_file.is_file():
            raise SiteConfigError("Redirect destination does not exist.")
        pending[destination] = url
    for destination, url in pending.items():
        safe_url = escape(url, quote=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            '<title>Page moved</title><meta name="robots" content="noindex">\n'
            f'<link rel="canonical" href="{safe_url}">\n'
            f'<meta http-equiv="refresh" content="0;url={safe_url}">\n'
            "</head><body><p>This page has moved. "
            f'<a href="{safe_url}">Visit the Writing collection</a>.</p></body></html>\n',
            encoding="utf-8",
        )
    return list(pending)
