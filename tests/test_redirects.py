"""Legacy links must remain inside the Pages subpath, without overwriting pages."""

import pytest
import yaml

from tests.helpers import make_site_root
from tools.redirects import write_redirects
from tools.site_config import SiteConfigError, load_site_config


def test_redirect_has_canonical_and_fallback(tmp_path):
    root = make_site_root(tmp_path)
    (root / "config/redirects.yml").write_text("redirects:\n  old/: writing/\n")
    config = load_site_config(root)
    target = config.output_dir / "writing/index.html"
    target.parent.mkdir(parents=True)
    target.write_text("<h1>Writing</h1>")
    created = write_redirects(config)
    assert created == [config.output_dir / "old/index.html"]
    html = created[0].read_text()
    assert "https://example.test/keep-it-simple/writing/" in html
    assert 'rel="canonical"' in html
    assert "<a href=" in html
    assert 'http-equiv="refresh"' in html


@pytest.mark.parametrize(
    "mapping",
    [
        {"../outside/": "writing/"},
        {"old/": "/writing/"},
        {"old/": "old/"},
        {"old/": "writing/", "old": "writing/"},
    ],
)
def test_unsafe_or_ambiguous_redirects_fail_without_writes(tmp_path, mapping):
    root = make_site_root(tmp_path)
    (root / "config/redirects.yml").write_text(yaml.safe_dump({"redirects": mapping}))
    config = load_site_config(root)
    with pytest.raises(SiteConfigError):
        write_redirects(config)
    assert not (root / "outside").exists()


def test_redirect_does_not_overwrite_real_page(tmp_path):
    root = make_site_root(tmp_path)
    (root / "config/redirects.yml").write_text("redirects:\n  old/: writing/\n")
    config = load_site_config(root)
    target = config.output_dir / "old/index.html"
    target.parent.mkdir(parents=True)
    target.write_text("real content")
    with pytest.raises(SiteConfigError):
        write_redirects(config)
    assert target.read_text() == "real content"
