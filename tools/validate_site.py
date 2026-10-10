"""Validate the supported public authoring surface and generated local links.

This is an accidental-publication guard, not a sandbox for arbitrary extensions.
Custom engines/filters/hooks and active shortcodes other than video are excluded.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from fnmatch import fnmatchcase
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from .documents import DocumentError, load_mapping, load_yaml, read_document
from .site_config import SiteConfig

RESERVED = {
    ".personal",
    ".agent",
    ".git",
    ".venv",
    ".local",
    ".superpowers",
    ".cache",
    ".quarto",
    ".idea",
    ".vscode",
    ".ssh",
    ".aws",
    ".gnupg",
    ".kube",
    "_site",
}
SENSITIVE_FILE_PATTERNS = (
    ".env",
    ".env.*",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_dsa*",
    "id_ecdsa*",
    "id_ed25519*",
    "*credentials*.json",
    "*secrets*.json",
    "*secrets*.yml",
    "*secrets*.yaml",
    "service-account*.json",
    "service_account*.json",
)
FILE_KEYS = {
    "path",
    "bibliography",
    "csl",
    "resources",
    "css",
    "metadata-files",
    "image",
    "logo",
    "favicon",
    "include-before-body",
    "include-after-body",
    "include-in-header",
    "render",
}
MARKDOWN_FILE_KEYS = {"body-header", "body-footer", "margin-header", "margin-footer"}
UNSUPPORTED = {
    "filters",
    "engine",
    "jupyter",
    "knitr",
    "pre-render",
    "post-render",
    "pandoc-args",
    "template",
}
SHORTCODE = re.compile(r"\{\{[<%](.*?)[>%]\}\}", re.S)
MARKDOWN = MarkdownIt("commonmark")


class ValidationError(ValueError):
    """A production build must not be published."""


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.refs: list[tuple[str, bool]] = []
        self.cites: set[str] = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "a" and data.get("name"):
            self.ids.add(data["name"])
        for attribute in ("href", "src", "poster"):
            if data.get(attribute):
                self.refs.append(
                    (data[attribute], tag == "link" and data.get("rel") == "canonical")
                )
        if data.get("srcset") and not data["srcset"].lstrip().startswith("data:"):
            for candidate in data["srcset"].split(","):
                if candidate.strip():
                    self.refs.append((candidate.strip().split()[0], False))
        if tag == "meta":
            content = data.get("content", "")
            if data.get("property") == "og:url" or data.get("name") == "twitter:url":
                self.refs.append((content, True))
            if data.get("http-equiv", "").lower() == "refresh":
                match = re.search(r"url\s*=\s*(.+)", content, re.I)
                if match:
                    self.refs.append((match[1].strip("\"' "), True))
        if "citation" in data.get("class", "").split():
            self.cites.update(data.get("data-cites", "").split())


def _sensitive_path(path: Path) -> bool:
    """Conservative filename guard, not a substitute for scanning file contents."""
    return any(
        fnmatchcase(part.lower(), pattern)
        for part in path.parts
        for pattern in SENSITIVE_FILE_PATTERNS
    )


def _source_ref(config, source, value, *, glob=False, site_absolute=True, local_only=False):
    if not isinstance(value, str) or not value:
        raise ValidationError("File references must be nonempty strings.")
    excluded = glob and value.startswith("!")
    value = value[1:] if excluded else value
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        if not local_only and parsed.scheme in {"http", "https", "mailto", "tel", "data"}:
            return
        raise ValidationError("Unsupported external file reference.")
    if not value or value.startswith("#"):
        return
    raw = value if glob else unquote(parsed.path)
    if "\\" in raw or "\x00" in raw or "${" in raw or "{{" in raw:
        raise ValidationError("Unsafe or dynamic file reference.")
    prefix = re.split(r"[*?\[]", raw, maxsplit=1)[0] if glob else raw
    if prefix.startswith("/"):
        if not site_absolute:
            raise ValidationError("Absolute filesystem references are not allowed.")
        candidate = config.docs_dir / prefix.lstrip("/")
    else:
        candidate = source.parent / (prefix or ".")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(config.docs_dir):
        raise ValidationError("Reference escapes docs.")
    relative = resolved.relative_to(config.docs_dir)
    if not excluded and RESERVED.intersection(relative.parts):
        raise ValidationError("Reference targets a reserved directory.")
    if not excluded and _sensitive_path(relative):
        raise ValidationError("Reference targets a sensitive file.")
    # Check lexical components as well, before any read through a symlink.
    lexical = candidate.absolute()
    for parent in [lexical, *lexical.parents]:
        if parent == config.docs_dir:
            break
        if parent.is_symlink():
            raise ValidationError("Symlink references are not allowed.")
    if not glob and not candidate.exists():
        raise ValidationError("Missing local resource or page.")


def _markdown_refs(text):
    refs: list[str] = []
    for token in MARKDOWN.parse(text):
        for child in token.children or []:
            if child.type in {"link_open", "image"}:
                refs.append(child.attrGet("href") or child.attrGet("src") or "")
            elif child.type == "html_inline":
                html = _HTML()
                html.feed(child.content)
                refs.extend(ref for ref, _ in html.refs)
        if token.type == "html_block":
            html = _HTML()
            html.feed(token.content)
            refs.extend(ref for ref, _ in html.refs)
    return refs


def _metadata(config, source, metadata, issues):
    if source.suffix == ".qmd" or source.name in {"_quarto.yml", "_metadata.yml"}:
        formats = metadata.get("format")
        if (
            formats is not None
            and formats != "html"
            and (not isinstance(formats, dict) or set(formats) != {"html"})
        ):
            issues.append(
                f"{source.relative_to(config.docs_dir)}: public builds support HTML only; "
                "export manuscripts/slides separately."
            )

    def check(value, key, *, markdown=False):
        values = value if isinstance(value, list) else [value]
        if value is False and key in {"image", "logo", "favicon"}:
            return
        for item in values:
            if markdown and isinstance(item, str) and item.lstrip().startswith("::: "):
                # Native fenced Markdown avoids page-relative decorator file resolution.
                for reference in _markdown_refs(item):
                    try:
                        _source_ref(config, source, reference)
                    except (ValidationError, ValueError) as exc:
                        issues.append(f"{source.relative_to(config.docs_dir)}: {key}: {exc}")
                continue
            try:
                _source_ref(
                    config,
                    source,
                    item,
                    glob=key in {"render", "resources", "contents"},
                    site_absolute=key in {"href", "image", "logo", "favicon"},
                    local_only=key not in {"href", "image", "logo", "favicon"},
                )
            except (ValidationError, ValueError) as exc:
                issues.append(f"{source.relative_to(config.docs_dir)}: {key}: {exc}")

    def walk(value, context=""):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in UNSUPPORTED:
                    issues.append(
                        f"{source.relative_to(config.docs_dir)}: unsupported {key} option."
                    )
                elif key == "draft" and (not isinstance(item, bool) or item):
                    issues.append(
                        f"{source.relative_to(config.docs_dir)}: move drafts outside docs."
                    )
                elif context == "execute" and key == "enabled" and item is not False:
                    issues.append(
                        f"{source.relative_to(config.docs_dir)}: computation must be disabled."
                    )
                elif key in MARKDOWN_FILE_KEYS or (
                    context == "sidebar" and key in {"header", "footer"}
                ):
                    check(item, key, markdown=True)
                elif (
                    key in FILE_KEYS
                    or key == "href"
                    or (key == "contents" and context == "listing")
                ):
                    check(item, key)
                elif key == "theme":
                    for theme in item.values() if isinstance(item, dict) else [item]:
                        for name in theme if isinstance(theme, list) else [theme]:
                            if isinstance(name, str) and ("/" in name or name.endswith(".scss")):
                                issues.append(
                                    f"{source.relative_to(config.docs_dir)}: "
                                    "use built-in themes and customize CSS."
                                )
                else:
                    walk(item, key)
        elif isinstance(value, list):
            for item in value:
                walk(item, context)

    walk(metadata)


def validate_sources(config: SiteConfig) -> list[str]:
    issues: list[str] = []
    for source in sorted(config.docs_dir.rglob("*")):
        relative = source.relative_to(config.docs_dir)
        if any(part in {"_site", ".quarto"} for part in relative.parts):
            continue
        if source.is_symlink():
            issues.append(f"{relative}: symlink source is not allowed.")
            continue
        if RESERVED.intersection(relative.parts):
            issues.append(f"{relative}: reserved source location.")
            continue
        if _sensitive_path(relative):
            issues.append(f"{relative}: sensitive files must stay outside docs.")
            continue
        if not source.is_file() or source.suffix not in {
            ".qmd",
            ".md",
            ".yml",
            ".yaml",
            ".html",
            ".css",
            ".svg",
        }:
            continue
        try:
            text = source.read_text(encoding="utf-8")
            for match in SHORTCODE.finditer(text):
                expression = match[1].strip()
                if expression.startswith("/*") and expression.endswith("*/"):
                    continue
                if not expression.startswith("video "):
                    issues.append(
                        f"{relative}: unsupported active shortcode; use explicit public resources."
                    )
            if source.suffix in {".yml", ".yaml"}:
                data = (
                    load_mapping(text)
                    if source.name in {"_quarto.yml", "_metadata.yml"}
                    else load_yaml(text)
                )
                _metadata(config, source, data, issues)
                continue
            if source.suffix == ".qmd":
                metadata, text = read_document(source)
                if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
                    issues.append(f"{relative}: page requires a title.")
                _metadata(config, source, metadata, issues)
            refs: list[str] = []
            if source.suffix in {".qmd", ".md"}:
                refs.extend(_markdown_refs(text))
            elif source.suffix in {".html", ".svg"}:
                html = _HTML()
                html.feed(text)
                refs.extend(ref for ref, _ in html.refs)
            elif source.suffix == ".css":
                refs.extend(re.findall(r"url\([\"']?([^\)\"']+)", text))
                refs.extend(re.findall(r"@import\s+[\"']([^\"']+)", text))
            for ref in refs:
                try:
                    _source_ref(config, source, ref)
                except (ValidationError, ValueError) as exc:
                    issues.append(f"{relative}: {exc}")
        except (OSError, UnicodeError, DocumentError) as exc:
            issues.append(f"{relative}: invalid source ({type(exc).__name__}).")
    return issues


def _output_target(config, source, reference, canonical=False):
    parsed = urlsplit(reference)
    base = urlsplit(config.site_url)
    if canonical and (parsed.scheme or parsed.netloc) and not reference.startswith(config.site_url):
        raise ValidationError("Publication URL uses the wrong site identity.")
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
            return None
        if not parsed.path.startswith(base.path):
            if canonical:
                raise ValidationError("Publication URL loses the project prefix.")
            return None  # Explicit absolute link to another project on the same host.
        path = config.output_dir / unquote(parsed.path[len(base.path) :])
    elif parsed.path.startswith("/"):
        if not parsed.path.startswith(base.path):
            raise ValidationError("Root-relative link loses the project prefix.")
        path = config.output_dir / unquote(parsed.path[len(base.path) :])
    else:
        path = source.parent / unquote(parsed.path) if parsed.path else source
    if not path.resolve().is_relative_to(config.output_dir.resolve()):
        raise ValidationError("Output link escapes the public site.")
    relative = path.resolve().relative_to(config.output_dir.resolve())
    if RESERVED.intersection(relative.parts):
        raise ValidationError("Output references reserved content.")
    if _sensitive_path(relative):
        raise ValidationError("Output references a sensitive file.")
    if path.is_dir() or parsed.path.endswith("/"):
        path /= "index.html"
    if not path.is_file():
        raise ValidationError(f"Missing output target: {relative.as_posix()}")
    return path, unquote(parsed.fragment)


def validate_output(config: SiteConfig) -> list[str]:
    issues: list[str] = []
    if not (config.output_dir / "index.html").is_file():
        issues.append("index.html: no public homepage was rendered.")
    pages: dict[Path, _HTML] = {}
    for path in sorted(config.output_dir.rglob("*")):
        relative = path.relative_to(config.output_dir)
        if path.is_symlink() or RESERVED.intersection(relative.parts):
            issues.append(f"{relative}: reserved or symlinked output.")
            continue
        if _sensitive_path(relative):
            issues.append(f"{relative}: sensitive file in public output.")
            continue
        if not path.is_file():
            continue
        if path.name in {"_quarto.yml", "_metadata.yml", "authors.yml"} or path.suffix == ".qmd":
            issues.append(f"{relative}: source/configuration leaked into output.")
        if path.suffix == ".html":
            parsed = _HTML()
            parsed.feed(path.read_text(encoding="utf-8"))
            pages[path.resolve()] = parsed

    def check(source, reference, canonical=False):
        try:
            result = _output_target(config, source, reference, canonical)
            if result is None:
                return
            target, fragment = result
            if (
                fragment
                and target.suffix == ".html"
                and not fragment.startswith(("category=", "author=", "date="))
            ):
                page = pages.get(target.resolve())
                if page is not None and fragment not in page.ids:
                    raise ValidationError(
                        f"Missing fragment in {target.relative_to(config.output_dir)}"
                    )
        except (ValidationError, ValueError) as exc:
            issues.append(f"{source.relative_to(config.output_dir)}: {exc}")

    for source, parsed in pages.items():
        for reference, canonical in parsed.refs:
            check(source, reference, canonical)
        for key in parsed.cites:
            if f"ref-{key}" not in parsed.ids:
                issues.append(f"{source.relative_to(config.output_dir)}: unresolved citation.")
    for path in config.output_dir.glob("*.xml"):
        try:
            tree = ET.parse(path)
            for element in tree.iter():
                if element.tag.rsplit("}", 1)[-1] in {"loc", "link"}:
                    value = element.get("href") or (element.text or "").strip()
                    if value:
                        check(path, value, canonical=True)
        except ET.ParseError:
            issues.append(f"{path.name}: malformed XML.")
    search = config.output_dir / "search.json"
    if search.exists():
        try:
            entries = json.loads(search.read_text(encoding="utf-8"))
            if not isinstance(entries, list):
                raise ValueError("Expected search entries.")
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get("href"), str):
                    raise ValueError("Invalid search entry.")
                check(search, entry["href"])
        except (ValueError, OSError):
            issues.append("search.json: malformed search index.")
    return issues
