"""Exercise the real CLI and file emission against a temporary repository."""

from functools import partial

from typer.testing import CliRunner

from tests.helpers import make_site_root
from tools import new_post, scaffold
from tools.documents import read_document


def test_cli_creates_a_quarto_draft(tmp_path, monkeypatch):
    root = make_site_root(tmp_path)
    monkeypatch.setattr(new_post, "REPO_ROOT", root)
    monkeypatch.setattr(new_post, "create_post", partial(scaffold.create_post, repo_root=root))
    monkeypatch.setattr(new_post, "load_author_ids", partial(scaffold.load_author_ids, root))
    result = CliRunner().invoke(
        new_post.app,
        [
            "--title",
            "CLI Example",
            "--author",
            "raxit",
            "--description",
            "A summary",
            "--categories",
            "Systems",
            "--tags",
            "test",
        ],
    )
    assert result.exit_code == 0, result.output
    metadata, _ = read_document(root / "drafts/cli-example/index.qmd")
    assert metadata["title"] == "CLI Example" and metadata["draft"] is True
    assert not (root / "docs/posts").exists()
