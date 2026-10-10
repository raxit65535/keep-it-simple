"""Quarto authoring, safe filenames, and explicit overwrite behavior."""

import datetime as dt

import pytest

from tests.helpers import make_site_root
from tools.documents import read_document
from tools.scaffold import PostSpec, ScaffoldError, create_post


def test_slug_derived_from_title():
    assert (
        PostSpec(title="Hello World Post", author="raxit", description="d").slug
        == "hello-world-post"
    )


def test_scaffold_emits_native_quarto(tmp_path):
    root = make_site_root(tmp_path)
    spec = PostSpec(
        title="Latency: p99 — λ",
        slug="latency",
        author="raxit",
        description="A multiline\nsummary",
        tags=["systems", "Research"],
        categories=["Research"],
        date=dt.date(2026, 10, 8),
        bibliography="latency.bib",
    )
    result = create_post(spec, repo_root=root)
    metadata, body = read_document(result.post_file)
    assert result.post_file == root / "drafts/latency/index.qmd"
    assert metadata["author"] == [{"name": "Raxit Solanki"}]
    assert metadata["title"] == "Latency: p99 — λ"
    assert metadata["description"] == "A multiline\nsummary"
    assert metadata["draft"] is True
    assert metadata["bibliography"] == "latency.bib"
    assert metadata["categories"] == ["Research", "systems"]
    assert "<!-- more -->" not in body
    assert result.img_dir.is_dir() and result.assets_dir.is_dir()
    original = result.post_file.read_bytes()
    with pytest.raises(ScaffoldError):
        create_post(spec, repo_root=root)
    assert result.post_file.read_bytes() == original


@pytest.mark.parametrize(
    "change",
    [
        {"author": "unknown"},
        {"title": ""},
        {"slug": "../escape"},
        {"draft": "false"},
        {"bibliography": "../../.personal/notes.bib"},
        {"tags": [42]},
    ],
)
def test_invalid_metadata_never_writes(tmp_path, change):
    root = make_site_root(tmp_path)
    values = {"title": "Title", "author": "raxit", "description": "Description"}
    values.update(change)
    with pytest.raises(ScaffoldError):
        create_post(PostSpec(**values), repo_root=root)
    assert not (root / "drafts").exists()


def test_overwrite_is_explicit(tmp_path):
    root = make_site_root(tmp_path)
    spec = PostSpec(title="Example", author="raxit", description="d", body="First")
    result = create_post(spec, repo_root=root)
    spec.body = "Revised"
    create_post(spec, overwrite=True, repo_root=root)
    assert "Revised" in result.post_file.read_text()


def test_symlinked_asset_directory_is_not_followed(tmp_path):
    root = make_site_root(tmp_path)
    destination = root / "drafts/example"
    destination.mkdir(parents=True)
    (destination / "assets").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ScaffoldError):
        create_post(PostSpec(title="Example", author="raxit", description="d"), repo_root=root)
    assert not (destination / "index.qmd").exists()


def test_explicit_output_root_stays_under_drafts(tmp_path):
    root = make_site_root(tmp_path)
    with pytest.raises(ScaffoldError):
        create_post(
            PostSpec(title="Example", author="raxit", description="d"),
            output_root=root / ".personal",
            repo_root=root,
        )
    assert not (root / ".personal").exists()
