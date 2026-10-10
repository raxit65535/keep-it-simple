"""Migration contracts: retain real profile/artifact data, not starter posts."""

from pathlib import Path

from tools.documents import read_document

ROOT = Path(__file__).resolve().parents[1]


def test_retired_posts_are_not_sources():
    assert not (ROOT / "docs/posts/inspiration/inspiration.md").exists()
    assert not (ROOT / "docs/posts/ubuntu/ubuntu-linux.md").exists()


def test_profile_retains_existing_education_and_employers():
    metadata, body = read_document(ROOT / "docs/about/index.qmd")
    assert metadata["title"]
    for value in (
        "California State University Fullerton",
        "Ganpat University",
        "Shipt",
        "Minted",
        "Globe Life",
        "Insight Data Science",
        "Pollak",
        "Ujobi",
        "eClinicalWorks",
    ):
        assert value in body


def test_project_records_link_real_artifacts_without_verified_claims():
    records = {
        "umatch": "https://github.com/raxit65535/umatch",
        "git-archive": "https://github.com/raxit65535/literate-garbanzo",
        "batch-recommendations": "https://github.com/raxit65535/Big-Data-FInals",
    }
    for slug, url in records.items():
        metadata, body = read_document(ROOT / f"docs/contributions/{slug}/index.qmd")
        assert metadata["kind"] == "project"
        assert metadata["evidence-status"] == "self-described"
        assert url in body
    _, talks = read_document(ROOT / "docs/talks/index.qmd")
    assert "JHGOzwrlW8s" in talks


def test_template_types_are_unpublished():
    for kind in ("post", "paper-analysis", "project", "publication", "talk"):
        metadata, _ = read_document(ROOT / f"templates/{kind}.qmd")
        assert metadata["draft"] is True
        assert metadata["kind"] == kind
