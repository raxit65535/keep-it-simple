"""Real LangGraph integration; only external retrieval is replaced."""

from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from research_agent import graph, publish  # noqa: E402
from research_agent.config import AgentConfig  # noqa: E402
from research_agent.models import Paper  # noqa: E402
from tests.helpers import make_site_root  # noqa: E402
from tools.documents import read_document  # noqa: E402


@pytest.mark.agent
def test_cli_reports_publication_refusal_without_traceback(monkeypatch):
    from typer.testing import CliRunner

    from research_agent import __main__ as cli

    class RefusedRun:
        def invoke(self, state):
            raise publish.PublishError("Unrelated staged changes exist.")

    monkeypatch.setattr(graph, "build_pipeline", lambda config: RefusedRun())
    result = CliRunner().invoke(cli.app, ["Topic", "--author", "raxit", "--no-llm", "--no-dry-run"])
    assert result.exit_code == 1
    assert "Unrelated staged changes" in result.output
    assert isinstance(result.exception, SystemExit)


@pytest.mark.agent
def test_offline_graph_emits_quarto_bundle(tmp_path, monkeypatch):
    root = make_site_root(tmp_path)
    monkeypatch.setattr(graph, "REPO_ROOT", root)
    monkeypatch.setattr(publish, "REPO_ROOT", root)
    monkeypatch.setattr(graph, "RUNS_DIR", root / ".agent/runs")
    config = AgentConfig(use_llm=False)
    paper = Paper(
        title="Fixture paper",
        authors=["Example Author"],
        year=config.current_year(),
        venue="ICML",
        citation_count=100,
    )
    monkeypatch.setattr(graph, "search_arxiv", lambda *a, **kw: [paper])
    monkeypatch.setattr(graph, "search_semantic_scholar", lambda *a, **kw: [])
    monkeypatch.setattr(graph, "enrich_by_arxiv", lambda p: p)
    # The real dry-run publisher must perform no external actions.
    state = graph.build_pipeline(config).invoke(
        {
            "hypothesis": "A synthetic question",
            "title": "Fixture review",
            "author": "raxit",
            "categories": ["Research"],
            "tags": [],
            "dry_run": True,
        }
    )
    assert state["pr_url"] is None
    assert state["post_url"] == "https://example.test/keep-it-simple/posts/fixture-review/"
    post = next(Path(p) for p in state["created_paths"] if p.endswith("index.qmd"))
    metadata, body = read_document(post)
    assert metadata["ai-assisted"] is False
    assert metadata["draft"] is True and metadata["bibliography"] == "fixture-review.bib"
    assert "Unverified" in body
    run = Path(state["run_dir"])
    assert (run / "candidates.json").exists() and (run / "kept.json").exists()
    assert not (root / "docs/posts").exists()
    assert graph._run_dir("same-title") != graph._run_dir("same-title")
