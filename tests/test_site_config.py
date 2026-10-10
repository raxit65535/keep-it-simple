"""Configuration is a boundary: never lose the Pages subpath or escape a root."""

import pytest
import yaml

from tests.helpers import make_site_root
from tools.site_config import SiteConfigError, load_site_config, safe_target, validate_slug


def test_public_url_preserves_project_path(tmp_path):
    config = load_site_config(make_site_root(tmp_path))
    assert config.published_url("posts/example/") == (
        "https://example.test/keep-it-simple/posts/example/"
    )
    assert config.authors["raxit"]["name"] == "Raxit Solanki"


@pytest.mark.parametrize(
    "path", ["/posts/x", "../x", "https://evil.test/", "a?x=1", "a#x", "%2e%2e/x"]
)
def test_public_url_rejects_unsafe_paths(tmp_path, path):
    with pytest.raises(SiteConfigError):
        load_site_config(make_site_root(tmp_path)).published_url(path)


@pytest.mark.parametrize("slug", ["", "../x", "/x", "a/b", "a\\b", "a--b", "a b", "Upper"])
def test_invalid_slugs_are_rejected(slug):
    with pytest.raises(SiteConfigError):
        validate_slug(slug)


@pytest.mark.parametrize("path", ["", "../x", "/x", "a/../b", "a\\b", "./x"])
def test_safe_target_rejects_traversal(tmp_path, path):
    with pytest.raises(SiteConfigError):
        safe_target(tmp_path, path)
    assert list(tmp_path.iterdir()) == []


def test_safe_target_rejects_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "escape").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(SiteConfigError, match="symlink"):
        safe_target(root, "escape/file.txt")


@pytest.mark.parametrize(
    "url",
    ["http://example.test/", "https://user:secret@example.test/", "https://example.test/?token=x"],
)
def test_config_rejects_unsafe_site_identity(tmp_path, url):
    root = make_site_root(tmp_path)
    path = root / "docs/_quarto.yml"
    config = yaml.safe_load(path.read_text())
    config["website"]["site-url"] = url
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(SiteConfigError):
        load_site_config(root)


def test_config_rejects_unsafe_output_before_writing(tmp_path):
    root = make_site_root(tmp_path)
    path = root / "docs/_quarto.yml"
    config = yaml.safe_load(path.read_text())
    config["project"]["output-dir"] = "../.personal"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(SiteConfigError):
        load_site_config(root)
    assert not (root / ".personal").exists()
