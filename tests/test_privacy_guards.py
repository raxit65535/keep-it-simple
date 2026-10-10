"""Prevent private decorator imports and sensitive files entering public artifacts."""

import shutil

import pytest
import yaml

from tests.helpers import make_site_root
from tools.build_site import build_site
from tools.site_config import load_site_config
from tools.validate_site import ValidationError, validate_output, validate_sources

DECORATORS = (
    "sidebar.header",
    "sidebar.footer",
    "body-header",
    "body-footer",
    "margin-header",
    "margin-footer",
)
SENSITIVE_PATHS = (
    ".env",
    ".env.local",
    ".env.production",
    ".env.example",
    "assets/.ENV.LOCAL",
    "assets/client.pem",
    "assets/client.key",
    "assets/client.p12",
    "assets/client.pfx",
    "assets/id_ed25519",
    "assets/credentials.json",
    "assets/application_default_credentials.json",
    "assets/service-account-test.json",
    "assets/secrets.yml",
    "assets/.aws/credentials",
)


def set_decorator(root, field, value):
    path = root / "docs/_quarto.yml"
    metadata = yaml.safe_load(path.read_text())
    if field.startswith("sidebar."):
        metadata["website"]["sidebar"] = {
            "contents": [{"href": "index.qmd"}],
            field.split(".")[1]: value,
        }
    else:
        metadata["website"][field] = value
    path.write_text(yaml.safe_dump(metadata))


@pytest.mark.parametrize("field", DECORATORS)
def test_decorator_files_cannot_read_outside_docs(tmp_path, field):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\nPublic text.\n")
    (root / ".personal").mkdir()
    (root / ".personal/note.md").write_text("SYNTHETIC_PRIVATE_CONTENT")
    set_decorator(root, field, "../.personal/note.md")
    issues = validate_sources(load_site_config(root))
    assert issues, field
    assert not any("SYNTHETIC_PRIVATE_CONTENT" in issue for issue in issues)


@pytest.mark.parametrize("field", DECORATORS)
def test_decorator_file_references_check_existence(tmp_path, field):
    root = make_site_root(tmp_path)
    page = root / "docs/index.qmd"
    page.write_text("---\ntitle: Public\n---\nPublic text.\n")
    public = root / "docs/footer.md"
    public.write_text("Public footer.\n")
    set_decorator(root, field, "footer.md")
    assert validate_sources(load_site_config(root)) == []
    public.unlink()
    assert validate_sources(load_site_config(root)), field


@pytest.mark.parametrize("field", DECORATORS)
def test_inline_decorator_links_check_public_targets(tmp_path, field):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\nPublic text.\n")
    target = root / "docs/about.qmd"
    target.write_text("---\ntitle: About\n---\nPublic bio.\n")
    set_decorator(root, field, "::: {.public-note}\n[About](/about.qmd)\n:::\n")
    assert validate_sources(load_site_config(root)) == []
    target.unlink()
    assert validate_sources(load_site_config(root)), field


@pytest.mark.parametrize("field", DECORATORS)
@pytest.mark.parametrize(
    "content",
    ["[Private](../.personal/note.md)", '<img src="../.personal/note.md" alt="Private">'],
)
def test_inline_decorators_reject_private_links(tmp_path, field, content):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\nPublic text.\n")
    set_decorator(root, field, f"::: {{.public-note}}\n{content}\n:::\n")
    assert validate_sources(load_site_config(root)), field


def test_sidebar_footer_list_checks_every_file(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\n")
    (root / "docs/footer.md").write_text("Public footer.\n")
    set_decorator(root, "sidebar.footer", ["footer.md", "../.personal/note.md"])
    assert validate_sources(load_site_config(root))


@pytest.mark.parametrize("name", SENSITIVE_PATHS)
def test_sensitive_files_are_rejected_even_when_unreferenced(tmp_path, name):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\n")
    path = root / "docs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("SYNTHETIC_PRIVATE_CONTENT")
    issues = validate_sources(load_site_config(root))
    assert issues, name
    assert not any("SYNTHETIC_PRIVATE_CONTENT" in issue for issue in issues)


@pytest.mark.parametrize("name", SENSITIVE_PATHS)
def test_sensitive_output_files_are_rejected(tmp_path, name):
    config = load_site_config(make_site_root(tmp_path))
    config.output_dir.mkdir()
    (config.output_dir / "index.html").write_text("<h1>Public</h1>")
    path = config.output_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("SYNTHETIC_PRIVATE_CONTENT")
    issues = validate_output(config)
    assert issues, name
    assert not any("SYNTHETIC_PRIVATE_CONTENT" in issue for issue in issues)


def test_public_assets_and_pages_markers_remain_allowed(tmp_path):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\n")
    (root / "docs/assets").mkdir()
    (root / "docs/assets/data.json").write_text('{"public": true}')
    (root / "docs/assets/public-key-explanation.md").write_text("Public explanation.")
    assert validate_sources(load_site_config(root)) == []
    config = load_site_config(root)
    config.output_dir.mkdir()
    (config.output_dir / "index.html").write_text("<h1>Public</h1>")
    (config.output_dir / ".nojekyll").touch()
    assert validate_output(config) == []


@pytest.mark.quarto
@pytest.mark.parametrize("case", ["footer", "env-resource"])
def test_strict_build_refuses_private_payload_before_rendering(tmp_path, case):
    if shutil.which("quarto") is None:
        pytest.skip("Pinned Quarto is required to reproduce the former leak")
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\nPublic text.\n")
    if case == "footer":
        (root / ".personal").mkdir()
        (root / ".personal/note.md").write_text("SYNTHETIC_PRIVATE_CONTENT")
        set_decorator(root, "sidebar.footer", "../.personal/note.md")
    else:
        (root / "docs/.env.local").write_text("SYNTHETIC_PRIVATE_CONTENT")
        path = root / "docs/_quarto.yml"
        metadata = yaml.safe_load(path.read_text())
        metadata["project"]["resources"] = [".env.local"]
        path.write_text(yaml.safe_dump(metadata))
    with pytest.raises(ValidationError):
        build_site(root)
    assert not (root / "docs/_site").exists()
