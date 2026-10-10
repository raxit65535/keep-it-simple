"""Strict YAML/front matter without leaking source excerpts in diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class DocumentError(ValueError):
    """Malformed or ambiguous document metadata."""


class _UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise DocumentError("YAML keys must be strings.")
            if key in mapping:
                raise DocumentError(f"YAML duplicate key at line {key_node.start_mark.line + 1}.")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_yaml(text: str) -> Any:
    """Parse safe YAML, including native Quarto listing-data sequences."""
    try:
        value = yaml.load(text, Loader=_UniqueLoader)
    except DocumentError:
        raise
    except (yaml.YAMLError, ValueError, TypeError, KeyError) as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}" if mark else ""
        raise DocumentError(f"Invalid YAML{where}.") from None
    return value


def load_mapping(text: str) -> dict[str, Any]:
    """Require a YAML mapping without allowing ambiguous keys."""
    value = load_yaml(text)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DocumentError("YAML must be a mapping.")
    return value


def read_document(path: Path) -> tuple[dict[str, Any], str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise DocumentError("Document requires leading YAML front matter.")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return load_mapping("".join(lines[1:index])), "".join(lines[index + 1 :]).lstrip("\n")
    raise DocumentError("Front matter requires a closing delimiter.")


def render_document(metadata: dict[str, Any], body: str) -> str:
    front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    return f"---\n{front}---\n\n{body.rstrip()}\n"
