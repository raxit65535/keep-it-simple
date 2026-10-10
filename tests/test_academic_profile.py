"""Professional collection contracts: navigable empty states, not invented records."""

import shutil
from pathlib import Path

import pytest

from tools.build_site import build_site
from tools.documents import read_document

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = ("publications", "service", "recognition", "awards", "memberships", "media")


def test_professional_collections_declare_their_record_state():
    for collection in COLLECTIONS:
        page = ROOT / f"docs/{collection}/index.qmd"
        metadata, body = read_document(page)
        assert metadata["record-status"] in {"awaiting-entries", "populated"}
        assert metadata.get("draft", False) is False
        if metadata["record-status"] == "awaiting-entries":
            assert "collection-empty" in body
            assert "[@" not in body  # No example citations in an empty collection.


def test_forked_projects_record_upstream_attribution():
    for project, upstream in (
        ("git-archive", "https://github.com/drfloob/literate-garbanzo"),
        ("batch-recommendations", "https://github.com/Shashwat21/Big-Data-FInals"),
    ):
        metadata, body = read_document(ROOT / f"docs/contributions/{project}/index.qmd")
        assert metadata["project-origin"] == "fork"
        assert upstream in body


@pytest.mark.quarto
def test_academic_sections_render_with_links_from_the_homepage(tmp_path):
    if shutil.which("quarto") is None:
        pytest.skip("Pinned Quarto is required")
    snapshot = tmp_path / "site"
    snapshot.mkdir()
    shutil.copytree(
        ROOT / "docs", snapshot / "docs", ignore=shutil.ignore_patterns("_site", ".quarto")
    )
    shutil.copytree(ROOT / "config", snapshot / "config")
    shutil.copy2(ROOT / ".quarto-version", snapshot / ".quarto-version")
    private = snapshot / ".personal"
    private.mkdir()
    marker = "PRIVATE_NOTE_NOT_FOR_PUBLICATION"
    (private / "synthetic.md").write_text(marker)
    output = build_site(snapshot)
    home = (output / "index.html").read_text()
    # A global file-based header used to render only at the homepage's depth.
    for route in ("index.html", "publications/index.html", "contributions/umatch/index.html"):
        html = (output / route).read_text()
        sidebar = html.partition('<nav id="quarto-sidebar"')[2].partition("</nav>")[0]
        assert 'class="profile-facts"' in sidebar, route
        assert 'class="profile-links"' in sidebar, route
    for collection in COLLECTIONS:
        assert (output / collection / "index.html").is_file()
        assert f"{collection}/index.html" in home
    assert "contributions/research-workflows/index.html" in home
    assert "profile.jpg" in home
    assert ".personal/" not in home
    for path in output.rglob("*"):
        if path.is_file() and path.suffix in {".html", ".json", ".xml"}:
            assert marker not in path.read_text(), path.relative_to(output)
