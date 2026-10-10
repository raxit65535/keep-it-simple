"""LangGraph pipeline: search -> screen -> synthesize -> store -> publish."""

# LangGraph accumulates state across nodes, so every key is present by the time a
# node reads it. Suppress pyright's not-required-access false positives for this file.
# pyright: reportTypedDictNotRequiredAccess=false

from __future__ import annotations

import datetime as _dt
import json
import tempfile
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph
from slugify import slugify

from tools.scaffold import PostSpec
from tools.site_config import validate_slug

from .artifacts import write_draft_bundle
from .config import REPO_ROOT, RUNS_DIR, AgentConfig
from .credibility import dedupe, screen
from .models import Paper
from .sources.arxiv_source import search_arxiv
from .sources.semanticscholar import enrich_by_arxiv, search_semantic_scholar
from .writing import synthesize_review


class RunState(TypedDict, total=False):
    hypothesis: str
    title: str
    author: str
    categories: list[str]
    tags: list[str]
    dry_run: bool

    slug: str
    run_dir: str
    candidates: list[dict]
    kept: list[dict]
    body: str
    created_paths: list[str]
    post_url: str
    pr_url: str | None


def _run_dir(slug: str) -> Path:
    stamp = _dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    validate_slug(slug)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{stamp}-{slug}-", dir=RUNS_DIR))


def build_pipeline(config: AgentConfig):
    """Compile and return the research LangGraph."""

    def search_node(state: RunState) -> RunState:
        slug = slugify(state["title"])
        run_dir = _run_dir(slug)
        query = state["hypothesis"]

        candidates = search_arxiv(query, max_results=config.max_candidates)
        candidates += search_semantic_scholar(query, limit=config.max_candidates)
        candidates = dedupe(candidates)

        (run_dir / "candidates.json").write_text(
            json.dumps([p.model_dump() for p in candidates], indent=2),
            encoding="utf-8",
        )
        return {
            "slug": slug,
            "run_dir": str(run_dir),
            "candidates": [p.model_dump() for p in candidates],
        }

    def screen_node(state: RunState) -> RunState:
        candidates = [Paper(**d) for d in state["candidates"]]
        for paper in candidates:
            if paper.source == "arxiv" and paper.citation_count is None:
                enrich_by_arxiv(paper)
        kept = screen(candidates, config)

        run_dir = Path(state["run_dir"])
        (run_dir / "kept.json").write_text(
            json.dumps([p.model_dump() for p in kept], indent=2), encoding="utf-8"
        )
        return {"kept": [p.model_dump() for p in kept]}

    def synthesize_node(state: RunState) -> RunState:
        kept = [Paper(**d) for d in state["kept"]]
        body = synthesize_review(state["hypothesis"], kept, config)
        return {"body": body}

    def store_node(state: RunState) -> RunState:
        kept = [Paper(**d) for d in state["kept"]]
        spec = PostSpec(
            title=state["title"],
            author=state["author"],
            description=state["hypothesis"][:160],
            categories=state.get("categories", []),
            tags=state.get("tags", []),
            slug=state["slug"],
            body=state["body"],
            ai_assisted=config.use_llm,
        )
        bundle = write_draft_bundle(
            spec, kept, run_id=Path(state["run_dir"]).name, repo_root=REPO_ROOT
        )
        return {
            "post_url": bundle.post_url,
            "created_paths": [str(path) for path in bundle.files],
        }

    def publish_node(state: RunState) -> RunState:
        from .publish import open_pull_request

        paths = [Path(p) for p in state["created_paths"]]
        pr_url = open_pull_request(
            slug=state["slug"],
            title=state["title"],
            paths=paths,
            dry_run=state.get("dry_run", True),
        )
        return {"pr_url": pr_url}

    graph = StateGraph(RunState)
    graph.add_node("search", search_node)
    graph.add_node("screen", screen_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("store", store_node)
    graph.add_node("publish", publish_node)

    graph.set_entry_point("search")
    graph.add_edge("search", "screen")
    graph.add_edge("screen", "synthesize")
    graph.add_edge("synthesize", "store")
    graph.add_edge("store", "publish")
    graph.add_edge("publish", END)

    return graph.compile()
