"""Interactive Quarto authoring: uv run python -m tools.new_post."""

from __future__ import annotations

import typer

from tools.scaffold import REPO_ROOT, PostSpec, ScaffoldError, create_post, load_author_ids
from tools.site_config import SiteConfigError

app = typer.Typer(add_completion=False, help="Scaffold a Quarto draft outside the public site.")


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@app.command()
def main(
    title: str = typer.Option(..., prompt="Post title"),
    author: str = typer.Option("", help="Author id from config/authors.yml"),
    description: str = typer.Option(..., prompt="One-line description"),
    categories: str = typer.Option("", help="Comma-separated categories"),
    tags: str = typer.Option("", help="Comma-separated tags"),
    overwrite: bool = typer.Option(False, help="Explicitly replace an existing draft"),
) -> None:
    """Create drafts/<slug>/index.qmd and colocated img/ and assets/ folders."""
    try:
        authors = load_author_ids()
        if not author:
            author = typer.prompt(f"Author id {authors}", default=authors[0])
        if not categories:
            categories = typer.prompt("Categories (comma-separated)", default="")
        if not tags:
            tags = typer.prompt("Tags (comma-separated)", default="")
        spec = PostSpec(
            title=title,
            author=author,
            description=description,
            categories=_split_csv(categories),
            tags=_split_csv(tags),
        )
        result = create_post(spec, overwrite=overwrite)
    except (ScaffoldError, SiteConfigError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Created {result.post_file.relative_to(REPO_ROOT)}", fg=typer.colors.GREEN)
    typer.echo("Draft only: preview with Quarto; review before moving the bundle into docs/posts/.")
    typer.echo(
        "Set draft: false only for approved public content. Description supplies the excerpt."
    )


if __name__ == "__main__":
    app()
