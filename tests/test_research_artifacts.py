"""Real draft bundle emission, with explicit authorship and a bounded file set."""

import pytest

from research_agent.artifacts import write_draft_bundle
from research_agent.models import Paper
from tests.helpers import make_site_root
from tools.documents import read_document
from tools.scaffold import PostSpec, ScaffoldError


@pytest.mark.parametrize("ai_assisted", [True, False])
def test_bundle_has_bibliography_and_correct_public_url(tmp_path, ai_assisted):
    root = make_site_root(tmp_path)
    paper = Paper(title="Example Study", authors=["A Researcher"], year=2025)
    spec = PostSpec(
        title="Review",
        author="raxit",
        description="A review",
        slug="review",
        ai_assisted=ai_assisted,
    )
    bundle = write_draft_bundle(spec, [paper], run_id="run-001", repo_root=root)
    metadata, body = read_document(bundle.post_file)
    assert metadata["bibliography"] == "review.bib"
    assert metadata["draft"] is True
    assert metadata["ai-assisted"] is ai_assisted
    assert "unverified" in body.lower()
    assert bundle.post_url == "https://example.test/keep-it-simple/posts/review/"
    assert all(path.is_relative_to(root / "drafts") for path in bundle.files)
    assert {path.name for path in bundle.files} == {
        "index.qmd",
        "review.bib",
        "sources.yml",
        "social.yml",
    }
    assert "researcher2025example" in (bundle.post_dir / "review.bib").read_text()
    original = bundle.post_file.read_bytes()
    with pytest.raises(ScaffoldError):
        write_draft_bundle(spec, [paper], run_id="run-001", repo_root=root)
    assert bundle.post_file.read_bytes() == original


def test_run_id_cannot_escape_or_include_neighbor_files(tmp_path):
    root = make_site_root(tmp_path)
    spec = PostSpec(title="Review", author="raxit", description="d")
    with pytest.raises(ScaffoldError):
        write_draft_bundle(spec, [], run_id="../.personal", repo_root=root)
    assert not (root / ".personal").exists()
    bundle = write_draft_bundle(spec, [], run_id="run-001", repo_root=root)
    neighbor = root / "drafts/unrelated.txt"
    neighbor.write_text("not part of the bundle")
    assert neighbor not in bundle.files
