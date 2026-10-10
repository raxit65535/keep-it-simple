"""CLI for the research-writing agent.

Run via `uv run --group agent python -m research_agent --help`.
"""

from __future__ import annotations

import typer

from tools.scaffold import ScaffoldError, load_author_ids
from tools.site_config import SiteConfigError

from .config import AgentConfig
from .publish import PublishError

app = typer.Typer(add_completion=False, help="Agentic research-writing pipeline.")


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@app.command()
def run(
    hypothesis: str = typer.Argument(..., help="Research hypothesis or topic to review."),
    title: str = typer.Option("", help="Post title (defaults to the hypothesis)."),
    author: str = typer.Option("", help="Author id from config/authors.yml."),
    categories: str = typer.Option("Research", help="Comma-separated categories."),
    tags: str = typer.Option("", help="Comma-separated tags."),
    provider: str = typer.Option("", help="LLM provider: ollama | openai."),
    model: str = typer.Option("", help="Model name override."),
    no_llm: bool = typer.Option(False, help="Skip the LLM; emit a deterministic draft."),
    dry_run: bool = typer.Option(
        True,
        help="Write local drafts only (default). --no-dry-run opens a review PR; never merges.",
    ),
    max_candidates: int = typer.Option(0, help="Override max candidate papers."),
    keep_top_k: int = typer.Option(0, help="Override number of papers to keep."),
) -> None:
    """Search, screen, synthesize, and stage a literature-review post."""
    authors = load_author_ids()
    author = author or (authors[0] if authors else "")
    if authors and author not in authors:
        typer.secho(
            f"Unknown author '{author}'. Registered: {', '.join(authors)}.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    config = AgentConfig()
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if max_candidates:
        config.max_candidates = max_candidates
    if keep_top_k:
        config.keep_top_k = keep_top_k
    config.use_llm = not no_llm

    try:
        from .graph import build_pipeline
    except ModuleNotFoundError as exc:
        if not exc.name or not exc.name.startswith(("langgraph", "langchain", "requests", "arxiv")):
            raise
        typer.secho("Install research dependencies: uv sync --frozen --group agent", err=True)
        raise typer.Exit(code=1) from exc

    pipeline = build_pipeline(config)
    typer.echo("Running research pipeline… (this can take a few minutes)")
    try:
        result = pipeline.invoke(
            {
                "hypothesis": hypothesis,
                "title": title or hypothesis,
                "author": author,
                "categories": _split_csv(categories),
                "tags": _split_csv(tags),
                "dry_run": dry_run,
            }
        )
    except (PublishError, ScaffoldError, SiteConfigError) as exc:
        typer.secho(f"Research stopped: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    kept = result.get("kept", [])
    typer.secho(f"Kept {len(kept)} papers.", fg=typer.colors.GREEN)
    for path in result.get("created_paths", []):
        typer.echo(f"  wrote {path}")
    if dry_run:
        typer.secho(
            "Dry run: draft files written outside docs; no PR opened. "
            "--no-dry-run starts a new run and opens a review PR.",
            fg=typer.colors.YELLOW,
        )
    elif result.get("pr_url"):
        typer.secho(f"Opened PR: {result['pr_url']}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
