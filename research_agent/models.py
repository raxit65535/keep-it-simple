"""Data models for papers flowing through the research pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A candidate research paper gathered from a source API."""

    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    abstract: str = ""
    url: str = ""
    doi: str | None = None
    arxiv_id: str | None = None
    citation_count: int | None = None
    source: str = ""  # "arxiv" | "semanticscholar"

    # Populated during screening.
    credibility_score: float = 0.0
    credibility_reasons: list[str] = Field(default_factory=list)
    kept: bool = False

    def citekey(self) -> str:
        """A stable BibTeX cite key: firstauthorYEARfirsttitleword."""
        first_author = "anon"
        if self.authors:
            first_author = self.authors[0].split()[-1].lower()
        year = str(self.year or "n.d.")
        first_word = "".join(c for c in self.title.split()[0].lower() if c.isalnum())
        key = f"{first_author}{year}{first_word}"
        return "".join(c for c in key if c.isalnum())

    def best_url(self) -> str:
        if self.url:
            return self.url
        if self.doi:
            return f"https://doi.org/{self.doi}"
        if self.arxiv_id:
            return f"https://arxiv.org/abs/{self.arxiv_id}"
        return ""
