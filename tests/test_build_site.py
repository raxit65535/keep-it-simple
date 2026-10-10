"""Render process is mocked only at the external executable boundary."""

import subprocess

import pytest

from tests.helpers import make_site_root
from tools.build_site import build_site, clean_output
from tools.site_config import load_site_config
from tools.validate_site import ValidationError


def test_clean_output_refuses_symlink(tmp_path):
    root = make_site_root(tmp_path)
    config = load_site_config(root)
    private = root / ".personal"
    private.mkdir()
    marker = private / "marker.txt"
    marker.write_text("DO_NOT_DELETE")
    config.output_dir.symlink_to(private, target_is_directory=True)
    with pytest.raises(ValidationError):
        clean_output(config)
    assert marker.read_text() == "DO_NOT_DELETE"


def test_clean_build_removes_stale_output(tmp_path, monkeypatch):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: New page\n---\nPublic.\n")
    output = root / "docs/_site"
    output.mkdir()
    (output / "ghost.html").write_text("DO_NOT_PUBLISH_SENTINEL")

    def renderer(command, **kwargs):
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "1.10.19\n", "")
        assert "--no-execute" in command
        assert command[command.index("--to") + 1] == "html"
        assert not (output / "ghost.html").exists()
        (output / "index.html").write_text("<h1>New page</h1>")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", renderer)
    assert build_site(root, quarto="fake-quarto") == output
    assert not (output / "ghost.html").exists()


@pytest.mark.parametrize(
    "warning",
    [
        "WARNING: fixture warning",
        "[WARNING] fixture warning",
        "\x1b[33m[WARNING]\x1b[0m fixture warning",
    ],
)
def test_render_warnings_block_publication(tmp_path, monkeypatch, warning):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text("---\ntitle: Public\n---\n")

    def renderer(command, **kwargs):
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "1.10.19\n", "")
        return subprocess.CompletedProcess(command, 0, "", warning)

    monkeypatch.setattr(subprocess, "run", renderer)
    with pytest.raises(ValidationError, match="warning"):
        build_site(root, quarto="fake-quarto")


def test_wrong_version_does_not_clean_existing_output(tmp_path, monkeypatch):
    root = make_site_root(tmp_path)
    output = root / "docs/_site"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("Keep until preflight passes")
    monkeypatch.setattr(
        subprocess, "run", lambda args, **kw: subprocess.CompletedProcess(args, 0, "0.1.0\n", "")
    )
    with pytest.raises(ValidationError, match="1.10.19"):
        build_site(root, quarto="fake-quarto")
    assert marker.exists()


def test_private_source_stops_before_render(tmp_path, monkeypatch):
    root = make_site_root(tmp_path)
    (root / "docs/index.qmd").write_text(
        "---\ntitle: Public\nbibliography: ../.personal/source.bib\n---\n"
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Unsafe source reached renderer")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ValidationError):
        build_site(root)
