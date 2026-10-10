"""Semantic Scholar search + citation/venue enrichment via the Graph API."""

from __future__ import annotations

import time

import requests

from ..models import Paper

API = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,year,venue,authors,externalIds,citationCount,url"


def _to_paper(item: dict) -> Paper:
    ext = item.get("externalIds") or {}
    return Paper(
        title=(item.get("title") or "").strip(),
        authors=[a.get("name", "") for a in item.get("authors") or []],
        year=item.get("year"),
        venue=item.get("venue") or None,
        abstract=(item.get("abstract") or "").strip(),
        url=item.get("url") or "",
        doi=ext.get("DOI"),
        arxiv_id=ext.get("ArXiv"),
        citation_count=item.get("citationCount"),
        source="semanticscholar",
    )


def search_semantic_scholar(query: str, limit: int = 30, timeout: int = 20) -> list[Paper]:
    """Search Semantic Scholar. Returns [] on network/rate-limit errors."""
    try:
        resp = requests.get(
            f"{API}/paper/search",
            params={"query": query, "limit": min(limit, 100), "fields": FIELDS},
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []
    return [_to_paper(item) for item in resp.json().get("data", [])]


def enrich_by_arxiv(paper: Paper, timeout: int = 20) -> Paper:
    """Fill in citation count / venue for an arXiv paper via Semantic Scholar."""
    if not paper.arxiv_id:
        return paper
    try:
        resp = requests.get(
            f"{API}/paper/arXiv:{paper.arxiv_id}",
            params={"fields": "citationCount,venue,year"},
            timeout=timeout,
        )
        if resp.status_code == 429:
            time.sleep(1)
            return paper
        resp.raise_for_status()
    except requests.RequestException:
        return paper
    data = resp.json()
    if paper.citation_count is None:
        paper.citation_count = data.get("citationCount")
    if not paper.venue or paper.venue == "arXiv":
        paper.venue = data.get("venue") or paper.venue
    return paper
