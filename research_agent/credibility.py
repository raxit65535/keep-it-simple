"""Credibility screening: keep only reputable computer-science artifacts."""

from __future__ import annotations

import re

from .config import AgentConfig
from .models import Paper

# Reputable CS venues (conferences + journals). Matched case-insensitively as
# substrings/acronyms against a paper's venue string.
REPUTABLE_VENUES: set[str] = {
    # ML / AI
    "neurips", "nips", "icml", "iclr", "aaai", "ijcai", "uai", "aistats", "colt",
    "jmlr", "tpami", "tmlr",
    # NLP
    "acl", "emnlp", "naacl", "coling", "tacl", "eacl",
    # Vision
    "cvpr", "iccv", "eccv", "bmvc",
    # Systems / DB / data
    "osdi", "sosp", "nsdi", "eurosys", "usenix", "sigmod", "vldb", "icde",
    "sigkdd", "kdd", "cikm", "wsdm", "sigir", "www", "the web conference",
    # Theory / PL / SE
    "stoc", "focs", "soda", "pldi", "popl", "oopsla", "icse", "fse", "issta",
    # Security / networking
    "ieee s&p", "oakland", "ccs", "ndss", "sigcomm", "infocom",
    # Journals
    "communications of the acm", "acm computing surveys", "ieee transactions",
}

PREPRINT_MARKERS = {"arxiv", "preprint", "corr"}


def _venue_reputable(venue: str | None) -> bool:
    if not venue:
        return False
    v = venue.lower()
    return any(name in v for name in REPUTABLE_VENUES)


def _is_preprint(venue: str | None) -> bool:
    if not venue:
        return True
    v = venue.lower()
    return any(marker in v for marker in PREPRINT_MARKERS)


def score_paper(paper: Paper, config: AgentConfig) -> tuple[float, list[str]]:
    """Return a 0..1 credibility score and human-readable reasons."""
    score = 0.0
    reasons: list[str] = []

    if _venue_reputable(paper.venue):
        score += 0.5
        reasons.append(f"Published at a reputable venue ({paper.venue}).")
    elif _is_preprint(paper.venue):
        score += 0.1
        reasons.append("Preprint / not yet peer-reviewed at a top venue.")

    cites = paper.citation_count
    if cites is not None:
        if cites >= 100:
            score += 0.35
            reasons.append(f"Highly cited ({cites} citations).")
        elif cites >= config.min_citations:
            score += 0.2
            reasons.append(f"Cited {cites} times.")
        else:
            reasons.append(f"Low citation count ({cites}).")

    if paper.year is not None:
        age = config.current_year() - paper.year
        if age <= config.recency_years:
            score += 0.15
            reasons.append(f"Recent ({paper.year}).")
        else:
            reasons.append(f"Older work ({paper.year}).")

    if not paper.abstract:
        score -= 0.1
        reasons.append("No abstract available.")

    return max(0.0, min(1.0, score)), reasons


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def dedupe(papers: list[Paper]) -> list[Paper]:
    """Merge duplicate papers across sources, preferring richer metadata."""
    by_key: dict[str, Paper] = {}
    for paper in papers:
        key = paper.doi or paper.arxiv_id or _norm_title(paper.title)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = paper
            continue
        # Prefer the record that carries a citation count / real venue.
        if existing.citation_count is None and paper.citation_count is not None:
            existing.citation_count = paper.citation_count
        if (not existing.venue or existing.venue == "arXiv") and paper.venue:
            existing.venue = paper.venue
        if not existing.abstract and paper.abstract:
            existing.abstract = paper.abstract
    return list(by_key.values())


def screen(papers: list[Paper], config: AgentConfig) -> list[Paper]:
    """Score, filter by credibility threshold, and keep the top-k papers."""
    for paper in papers:
        paper.credibility_score, paper.credibility_reasons = score_paper(paper, config)

    eligible = [p for p in papers if p.credibility_score >= config.min_credibility]
    eligible.sort(
        key=lambda p: (p.credibility_score, p.citation_count or 0),
        reverse=True,
    )
    kept = eligible[: config.keep_top_k]
    for paper in kept:
        paper.kept = True
    return kept
