"""Catch ambiguous front matter and unsafe parser diagnostics."""

import pytest

from tools.documents import DocumentError, load_mapping, read_document, render_document


@pytest.mark.parametrize("text", ["draft: true\ndraft: false", "a:\n  x: 1\n  x: 2"])
def test_duplicate_keys_are_rejected(text):
    with pytest.raises(DocumentError, match="duplicate"):
        load_mapping(text)


@pytest.mark.parametrize("text", ["- a\n- b", "42", "!!python/object:x {}", "a: [PRIVATE_SENTINEL"])
def test_invalid_yaml_is_sanitized(text):
    with pytest.raises(DocumentError) as error:
        load_mapping(text)
    assert "PRIVATE_SENTINEL" not in str(error.value)


def test_yaml_catalog_can_be_an_empty_sequence():
    from tools.documents import load_yaml

    assert load_yaml("[]") == []
    with pytest.raises(DocumentError):
        load_mapping("[]")


def test_front_matter_round_trip(tmp_path):
    path = tmp_path / "index.qmd"
    metadata = {"title": "Latency: p99\nunder load — λ", "draft": True, "tags": ["a: b"]}
    path.write_text(render_document(metadata, "## Body\n\nText.\n"), encoding="utf-8")
    actual, body = read_document(path)
    assert actual == metadata
    assert body.strip() == "## Body\n\nText."


def test_windows_line_endings(tmp_path):
    path = tmp_path / "index.qmd"
    path.write_bytes(b"---\r\ntitle: Example\r\n---\r\nBody.\r\n")
    metadata, body = read_document(path)
    assert metadata == {"title": "Example"}
    assert body.strip() == "Body."


@pytest.mark.parametrize(
    "text", ["No header", "---\ntitle: Missing delimiter", "---\n- sequence\n---"]
)
def test_invalid_document_is_rejected(tmp_path, text):
    path = tmp_path / "index.qmd"
    path.write_text(text)
    with pytest.raises(DocumentError):
        read_document(path)
