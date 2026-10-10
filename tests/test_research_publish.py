"""Git is real and temporary; only network-facing gh/push calls are replaced."""

import subprocess

import pytest

from research_agent import publish
from tests.helpers import make_site_root
from tools.documents import read_document


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def make_repo(tmp_path):
    root = make_site_root(tmp_path)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test Author")
    git(root, "config", "user.email", "test@example.test")
    (root / "README.md").write_text("baseline\n")
    (root / ".gitignore").write_text(".personal/\ndrafts/\n")
    git(root, "add", "--", "README.md", ".gitignore", "docs", "config", ".quarto-version")
    git(root, "commit", "-m", "baseline")
    return root


def make_bundle(root):
    directory = root / "drafts/run-001/review"
    values = {
        "index.qmd": "---\ntitle: Review\ndraft: true\nai-assisted: true\n---\nUnverified draft.\n",
        "review.bib": "@misc{fixture,title={Fixture}}\n",
        "assets/sources.yml": "sources: []\n",
        "assets/social.yml": "x: Fixture\n",
    }
    paths = []
    for name, text in values.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        paths.append(path)
    return paths


def test_dry_run_has_no_subprocess_or_publication_path_checks(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry run invoked a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert (
        publish.open_pull_request(
            slug="review", title="Review", paths=[tmp_path / "outside.qmd"], dry_run=True
        )
        is None
    )


@pytest.mark.parametrize("mode", ["staged", "unstaged", "untracked"])
def test_publish_preflight_preserves_unrelated_work(tmp_path, monkeypatch, mode):
    root = make_repo(tmp_path)
    paths = make_bundle(root)
    monkeypatch.setattr(publish, "REPO_ROOT", root)
    if mode == "untracked":
        (root / "unrelated file.txt").write_text("user work")
    else:
        (root / "README.md").write_text("user work")
        if mode == "staged":
            git(root, "add", "--", "README.md")
    before = (git(root, "rev-parse", "HEAD"), git(root, "diff", "--cached", "--binary"))
    with pytest.raises(publish.PublishError):
        publish.preflight_publication(root, paths, root / "docs/posts/review")
    assert (git(root, "rev-parse", "HEAD"), git(root, "diff", "--cached", "--binary")) == before
    assert not (root / "docs/posts/review").exists()


def test_destination_collision_has_no_git_side_effects(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    paths = make_bundle(root)
    destination = root / "docs/posts/review"
    destination.mkdir(parents=True)
    marker = destination / "index.qmd"
    marker.write_text("keep this existing page")

    def forbidden(*args, **kwargs):
        raise AssertionError("collision reached Git")

    monkeypatch.setattr(publish, "_git", forbidden)
    with pytest.raises(publish.PublishError, match="exists"):
        publish.preflight_publication(root, paths, destination)
    assert marker.read_text() == "keep this existing page"


@pytest.mark.parametrize("mode", ["detached", "branch-exists", "missing-gh"])
def test_preflight_errors_leave_repository_unchanged(tmp_path, monkeypatch, mode):
    root = make_repo(tmp_path)
    paths = make_bundle(root)
    monkeypatch.setattr(publish, "REPO_ROOT", root)
    if mode == "detached":
        git(root, "checkout", "--detach")
    elif mode == "branch-exists":
        git(root, "branch", "research/review")
    else:
        monkeypatch.setattr(publish, "_gh_available", lambda: False)
    head = git(root, "rev-parse", "HEAD")
    with pytest.raises(publish.PublishError):
        publish.preflight_publication(root, paths, root / "docs/posts/review")
    assert git(root, "rev-parse", "HEAD") == head
    assert not (root / "docs/posts/review").exists()


@pytest.mark.parametrize("mode", ["neighbor", "symlink", "extra", "duplicate", "private"])
def test_bundle_selection_is_exact_and_public_safe(tmp_path, mode):
    root = make_repo(tmp_path)
    paths = make_bundle(root)
    if mode == "neighbor":
        outside = root / "drafts/neighbor.txt"
        outside.write_text("not selected")
        paths.append(outside)
    elif mode == "symlink":
        paths[1].unlink()
        paths[1].symlink_to(root / "README.md")
    elif mode == "extra":
        (paths[0].parent / ".env").write_text("PRIVATE_SENTINEL")
    elif mode == "duplicate":
        paths.append(paths[0])
    else:
        private = root / ".personal/index.qmd"
        private.parent.mkdir()
        private.write_text("PRIVATE_SENTINEL")
        paths = [private]
    with pytest.raises(publish.PublishError):
        publish.validate_bundle_paths(paths, root)


@pytest.mark.parametrize("pr_failure", [False, True])
def test_publication_commits_only_site_bundle_and_reports_remote_failure(
    tmp_path, monkeypatch, pr_failure
):
    root = make_repo(tmp_path)
    paths = make_bundle(root)
    # Old ignored runs must not block a new run or enter its commit.
    old = root / "drafts/old-run/notes.md"
    old.parent.mkdir(parents=True)
    old.write_text("Not selected")
    monkeypatch.setattr(publish, "REPO_ROOT", root)
    original_run = subprocess.run
    external = []

    def external_boundary(command, **kwargs):
        if command[:2] == ["git", "push"]:
            external.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[0] == "gh":
            external.append(command)
            if command[1:3] == ["pr", "create"]:
                return subprocess.CompletedProcess(
                    command,
                    1 if pr_failure else 0,
                    "" if pr_failure else "https://example.test/pr/1\n",
                    "",
                )
            return subprocess.CompletedProcess(command, 0, "authenticated", "")
        return original_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", external_boundary)
    if pr_failure:
        with pytest.raises(publish.PublishError, match="pushed"):
            publish.open_pull_request(slug="review", title="Review", paths=paths, dry_run=False)
    else:
        assert (
            publish.open_pull_request(slug="review", title="Review", paths=paths, dry_run=False)
            == "https://example.test/pr/1"
        )
    assert git(root, "branch", "--show-current").strip() == "research/review"
    metadata, body = read_document(root / "docs/posts/review/index.qmd")
    assert metadata["draft"] is False and metadata["ai-assisted"] is True
    assert "Unverified" in body
    assert read_document(paths[0])[0]["draft"] is True
    changed = set(
        git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
    )
    assert changed == {
        "docs/posts/review/index.qmd",
        "docs/posts/review/review.bib",
        "docs/posts/review/assets/sources.yml",
        "docs/posts/review/assets/social.yml",
    }
    assert [call for call in external if call[:2] == ["git", "push"]] == [
        ["git", "push", "-u", "origin", "research/review"]
    ]
