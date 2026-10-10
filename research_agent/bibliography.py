"""Generate published artifacts for kept papers: BibTeX + sources.yml sidecar."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Paper


def _bibtex_entry(paper: Paper) -> str:
    entry_type = "article" if paper.doi else "misc"
    fields: dict[str, str] = {
        "title": paper.title,
        "author": " and ".join(paper.authors) if paper.authors else "Unknown",
    }
    if paper.year:
        fields["year"] = str(paper.year)
    if paper.venue:
        fields["journal" if entry_type == "article" else "howpublished"] = paper.venue
    if paper.doi:
        fields["doi"] = paper.doi
    if paper.arxiv_id:
        fields["eprint"] = paper.arxiv_id
        fields["archivePrefix"] = "arXiv"
    if paper.best_url():
        fields["url"] = paper.best_url()

    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items())
    return f"@{entry_type}{{{paper.citekey()},\n{body}\n}}"


def to_bibtex(papers: list[Paper]) -> str:
    """Render a BibTeX document for the given papers."""
    return "\n\n".join(_bibtex_entry(p) for p in papers) + "\n"


def write_bibliography(papers: list[Paper], post_dir: Path, slug: str) -> Path:
    """Write <slug>.bib beside the post and return its path."""
    bib_path = post_dir / f"{slug}.bib"
    bib_path.write_text(to_bibtex(papers), encoding="utf-8")
    return bib_path


def write_sources_yaml(papers: list[Paper], assets_dir: Path) -> Path:
    """Write a human-auditable provenance/credibility sidecar."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "citekey": p.citekey(),
            "title": p.title,
            "authors": p.authors,
            "year": p.year,
            "venue": p.venue,
            "citation_count": p.citation_count,
            "source": p.source,
            "doi": p.doi,
            "arxiv_id": p.arxiv_id,
            "url": p.best_url(),
            "credibility_score": round(p.credibility_score, 3),
            "credibility_reasons": p.credibility_reasons,
        }
        for p in papers
    ]
    path = assets_dir / "sources.yml"
    path.write_text(
        yaml.safe_dump({"sources": records}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path
