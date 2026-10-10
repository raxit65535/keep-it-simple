"""Tests for the research agent's pure logic (offline, no network/LLM)."""

from __future__ import annotations

from research_agent.bibliography import to_bibtex
from research_agent.config import AgentConfig
from research_agent.credibility import dedupe, score_paper, screen
from research_agent.models import Paper
from research_agent.social import generate_social_copy
from research_agent.writing import synthesize_review


def _paper(**kw) -> Paper:
    base = dict(title="Attention Is All You Need", authors=["Ashish Vaswani"], year=2017)
    base.update(kw)
    return Paper(**base)


def test_citekey_is_stable_and_alnum():
    p = _paper()
    assert p.citekey() == "vaswani2017attention"


def test_reputable_venue_and_citations_score_high():
    cfg = AgentConfig()
    p = _paper(venue="NeurIPS", citation_count=1000, year=cfg.current_year())
    score, reasons = score_paper(p, cfg)
    assert score >= 0.8
    assert any("reputable" in r.lower() for r in reasons)


def test_preprint_low_citations_scores_low():
    cfg = AgentConfig()
    p = _paper(venue="arXiv", citation_count=0, year=1990)
    score, _ = score_paper(p, cfg)
    assert score < cfg.min_credibility


def test_screen_keeps_top_k_reputable():
    cfg = AgentConfig()
    cfg.keep_top_k = 2
    papers = [
        _paper(title="A B", venue="ICML", citation_count=500, year=cfg.current_year()),
        _paper(title="C D", venue="CVPR", citation_count=300, year=cfg.current_year()),
        _paper(title="E F", venue="Unknown Workshop", citation_count=0, year=1980),
    ]
    kept = screen(papers, cfg)
    assert len(kept) == 2
    assert all(p.kept for p in kept)


def test_dedupe_merges_by_arxiv_id():
    a = _paper(arxiv_id="1706.03762", citation_count=None, venue="arXiv")
    b = _paper(arxiv_id="1706.03762", citation_count=90000, venue="NeurIPS")
    merged = dedupe([a, b])
    assert len(merged) == 1
    assert merged[0].citation_count == 90000


def test_bibtex_contains_citekey_and_title():
    bib = to_bibtex([_paper(doi="10.1/x", venue="NeurIPS")])
    assert "vaswani2017attention" in bib
    assert "Attention Is All You Need" in bib


def test_social_copy_respects_x_length():
    copy = generate_social_copy(
        "A very long title " * 10,
        "https://example.com/post/",
        "summary " * 40,
        tags=["ml", "nlp"],
    )
    assert len(copy["x"]) <= 280
    assert "linkedin" in copy


def test_offline_review_cites_kept_papers():
    cfg = AgentConfig()
    cfg.use_llm = False
    body = synthesize_review("Do transformers scale?", [_paper()], cfg)
    assert "[@vaswani2017attention]" in body
    assert "## Introduction" in body
