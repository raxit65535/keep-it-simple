"""Narrow integration checks of the actual pinned renderer."""

import shutil
from pathlib import Path

import pytest

from tests.helpers import make_site_root
from tools.build_site import build_site
from tools.validate_site import ValidationError


@pytest.mark.quarto
def test_empty_public_portfolio_builds_without_warnings(tmp_path):
    if shutil.which("quarto") is None:
        pytest.skip("Pinned Quarto is required for renderer integration")
    root = Path(__file__).resolve().parents[1]
    snapshot = tmp_path / "public"
    snapshot.mkdir()
    shutil.copytree(
        root / "docs", snapshot / "docs", ignore=shutil.ignore_patterns("_site", ".quarto")
    )
    shutil.copytree(root / "config", snapshot / "config")
    shutil.copy2(root / ".quarto-version", snapshot / ".quarto-version")
    output = build_site(snapshot)
    assert (output / "index.html").is_file()
    assert (output / "about/index.html").is_file()
    assert not (output / ".personal").exists()
    assert 'http-equiv="refresh"' in (output / "inspiration/index.html").read_text()


@pytest.mark.quarto
def test_research_bundle_renders_after_reviewed_promotion(tmp_path):
    if shutil.which("quarto") is None:
        pytest.skip("Pinned Quarto is required for renderer integration")
    from research_agent.artifacts import write_draft_bundle
    from research_agent.models import Paper
    from tools.documents import read_document, render_document
    from tools.scaffold import PostSpec

    root = make_site_root(tmp_path)
    bundle = write_draft_bundle(
        PostSpec(
            title="Review",
            author="raxit",
            description="A synthetic review",
            body="A result [@researcher2025fixture].",
            ai_assisted=True,
        ),
        [Paper(title="Fixture study", authors=["Test Researcher"], year=2025)],
        run_id="test-run",
        repo_root=root,
    )
    target = root / "docs/posts/review"
    shutil.copytree(bundle.post_dir, target)
    metadata, body = read_document(target / "index.qmd")
    metadata["draft"] = False
    (target / "index.qmd").write_text(render_document(metadata, body))
    output = build_site(root)
    html = (output / "posts/review/index.html").read_text()
    assert "ref-researcher2025fixture" in html
    assert "Unverified literature draft" in html


@pytest.mark.quarto
def test_native_render_and_missing_citation(tmp_path):
    if shutil.which("quarto") is None:
        pytest.skip("Pinned Quarto is required for renderer integration")
    root = make_site_root(tmp_path)
    docs = root / "docs"
    (docs / "figure.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">'
        '<rect width="40" height="20" fill="blue"/></svg>'
    )
    (docs / "refs.bib").write_text(
        "@article{fixture, title={Fixture study}, author={Example, Alice}, year={2020}}\n"
    )
    page = docs / "index.qmd"
    page.write_text(
        "---\ntitle: Fixture\nbibliography: refs.bib\n---\n"
        "A citation [@fixture] and $E=mc^2$.\n\n"
        "![Fixture](figure.svg)\n\n"
        '```python\nprint("example")\n```\n\n'
        "```{mermaid}\ngraph TD; A-->B\n```\n"
    )
    output = build_site(root)
    html = (output / "index.html").read_text()
    for marker in ("ref-fixture", "math", "mermaid", "figure.svg"):
        assert marker in html
    page.write_text(page.read_text().replace("[@fixture]", "[@missing]"))
    with pytest.raises(ValidationError):
        build_site(root)
