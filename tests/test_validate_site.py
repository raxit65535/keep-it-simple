"""Publication boundary tests use synthetic private data only."""

import json

import pytest
import yaml

from tests.helpers import make_site_root
from tools.site_config import load_site_config
from tools.validate_site import validate_output, validate_sources


@pytest.mark.parametrize(
    "body",
    [
        "![Image](../.personal/sentinel.txt)",
        '<img src="../.personal/sentinel.txt" alt="Image">',
        "[link][ref]\n\n[ref]: ../.personal/sentinel.txt",
        "{{< include ../.personal/sentinel.txt >}}",
        "```text\n{{< include ../.personal/sentinel.txt >}}\n```",
    ],
)
def test_source_references_cannot_escape_docs(tmp_path, body):
    root = make_site_root(tmp_path)
    (root / ".personal").mkdir()
    (root / ".personal/sentinel.txt").write_text("DO_NOT_PUBLISH_SENTINEL")
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\n" + body)
    issues = validate_sources(load_site_config(root))
    assert issues
    assert not any("DO_NOT_PUBLISH_SENTINEL" in issue for issue in issues)


@pytest.mark.parametrize("field", ["bibliography", "include-after-body", "metadata-files", "image"])
def test_file_metadata_cannot_escape_docs(tmp_path, field):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text(
        f"---\ntitle: Public\n{field}: ../.personal/sentinel.txt\n---\n"
    )
    assert validate_sources(load_site_config(root))


@pytest.mark.parametrize("field", ["resources", "render"])
def test_project_globs_cannot_escape_docs(tmp_path, field):
    root = make_site_root(tmp_path)
    path = root / "docs/_quarto.yml"
    config = yaml.safe_load(path.read_text())
    config["project"][field] = ["../.personal/**"]
    path.write_text(yaml.safe_dump(config))
    assert validate_sources(load_site_config(root))


@pytest.mark.parametrize("draft", ['"false"', "true"])
def test_quoted_draft_is_rejected(tmp_path, draft):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text(f"---\ntitle: Public\ndraft: {draft}\n---\n")
    assert validate_sources(load_site_config(root))


@pytest.mark.parametrize("format_value", ["pdf", "revealjs", {"html": {}, "pdf": {}}])
def test_public_render_rejects_other_toolchains(tmp_path, format_value):
    root = make_site_root(tmp_path)
    page = root / "docs/index.qmd"
    page.write_text("---\n" + yaml.safe_dump({"title": "Public", "format": format_value}) + "---\n")
    assert validate_sources(load_site_config(root))


def test_empty_output_is_not_a_valid_website(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    assert validate_output(config)


def test_symlink_source_is_rejected(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/leak.svg").symlink_to(tmp_path / "private.svg")
    assert validate_sources(load_site_config(root))


def test_normal_code_links_are_not_active(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text(
        "---\ntitle: Public\n---\n```markdown\n[example](not-a-real-file.md)\n```\n"
    )
    assert validate_sources(load_site_config(root)) == []


def test_sidebar_header_file_cannot_escape_docs(tmp_path):
    root = make_site_root(tmp_path)
    config_file = root / "docs/_quarto.yml"
    metadata = yaml.safe_load(config_file.read_text())
    metadata["website"]["sidebar"] = {"header": "../.personal/notes.md", "contents": []}
    config_file.write_text(yaml.safe_dump(metadata))
    assert validate_sources(load_site_config(root))


def test_inline_sidebar_markdown_checks_public_links(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/about.qmd").write_text("---\ntitle: About\n---\nPublic bio.\n")
    path = root / "docs/_quarto.yml"
    metadata = yaml.safe_load(path.read_text())
    metadata["website"]["sidebar"] = {
        "header": "::: {.profile-summary}\n[About](/about.qmd)\n:::\n",
        "contents": [],
    }
    path.write_text(yaml.safe_dump(metadata))
    assert validate_sources(load_site_config(root)) == []
    (root / "docs/about.qmd").unlink()
    assert validate_sources(load_site_config(root))


@pytest.mark.parametrize(
    "content",
    [
        "[Private](../.personal/notes.md)",
        '<img src="../.personal/notes.md" alt="Private">',
    ],
)
def test_inline_sidebar_cannot_reference_private_files(tmp_path, content):
    root = make_site_root(tmp_path)
    path = root / "docs/_quarto.yml"
    metadata = yaml.safe_load(path.read_text())
    metadata["website"]["sidebar"] = {
        "header": f"::: {{.profile-summary}}\n{content}\n:::\n",
        "contents": [],
    }
    path.write_text(yaml.safe_dump(metadata))
    assert validate_sources(load_site_config(root))


def test_reference_links_resolve_and_missing_ones_fail(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/image.svg").write_text("<svg/>")
    page = root / "docs/index.qmd"
    page.write_text("---\ntitle: Public\n---\n![image][figure]\n\n[figure]: image.svg\n")
    assert validate_sources(load_site_config(root)) == []
    (root / "docs/image.svg").unlink()
    assert validate_sources(load_site_config(root))


def test_output_links_keep_project_prefix(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "index.html").write_text('<a href="/about/">Bad</a>')
    assert validate_output(config)


def test_encoded_asset_and_fragment(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "figure one.png").write_bytes(b"fixture")
    (config.output_dir / "index.html").write_text(
        '<h2 id="results">Results</h2><a href="#results">Jump</a>'
        '<img src="figure%20one.png" alt="Figure">'
    )
    assert validate_output(config) == []


@pytest.mark.parametrize(
    "html",
    [
        '<a href="#missing">Broken</a>',
        '<img src="missing.svg">',
        '<link rel="canonical" href="https://wrong.test/">',
        '<meta property="og:url" content="https://wrong.test/">',
        '<a href="../.personal/notes.html">Private</a>',
    ],
)
def test_broken_or_wrong_identity_output_is_rejected(tmp_path, html):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "index.html").write_text(html)
    assert validate_output(config)


def test_relative_redirect_is_valid_but_external_redirect_is_not(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "target.html").write_text("<h1>Target</h1>")
    redirect = config.output_dir / "index.html"
    redirect.write_text('<meta http-equiv="refresh" content="0;URL=target.html">')
    assert validate_output(config) == []
    redirect.write_text('<meta http-equiv="refresh" content="0;URL=https://wrong.test/">')
    assert validate_output(config)


def test_search_and_sitemap_links_are_checked(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "index.html").write_text('<h1 id="home">Home</h1>')
    search = config.output_dir / "search.json"
    search.write_text(json.dumps([{"href": "index.html#home", "text": "Home"}]))
    (config.output_dir / "sitemap.xml").write_text(
        "<urlset><url><loc>https://example.test/keep-it-simple/</loc></url></urlset>"
    )
    assert validate_output(config) == []
    search.write_text(json.dumps([{"href": ".personal/leak.html"}]))
    assert validate_output(config)
