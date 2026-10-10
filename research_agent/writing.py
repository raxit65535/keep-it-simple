"""Synthesize a literature review from screened papers (LLM or offline)."""

from __future__ import annotations

from .config import AgentConfig
from .models import Paper

SYSTEM_PROMPT = (
    "You are a rigorous computer-science research writer. Write a clear, honest "
    "literature review for a technical blog. Ground every claim in the provided "
    "papers and cite them inline using the exact form [@citekey]. Do not invent "
    "citations, results, or papers. Be balanced about strengths and limitations."
)


def _papers_context(papers: list[Paper]) -> str:
    blocks = []
    for p in papers:
        blocks.append(
            f"[@{p.citekey()}] {p.title} ({p.year}, {p.venue or 'n/a'}; "
            f"citations={p.citation_count if p.citation_count is not None else 'n/a'})\n"
            f"Abstract: {p.abstract[:800]}"
        )
    return "\n\n".join(blocks)


def build_prompt(hypothesis: str, papers: list[Paper]) -> str:
    return (
        f"Hypothesis / topic:\n{hypothesis}\n\n"
        f"Papers you may cite (use the [@citekey] shown):\n{_papers_context(papers)}\n\n"
        "Write the review with these sections:\n"
        "## Introduction\n## What the literature says\n## Points of agreement and tension\n"
        "## Assessment of the hypothesis\n## Open questions\n\n"
        "Cite inline with [@citekey]. Output Quarto-compatible Markdown body only, "
        "without YAML front matter, file-inclusion shortcodes, or executable code cells."
    )


def _offline_review(hypothesis: str, papers: list[Paper]) -> str:
    """Deterministic, no-LLM draft body used for testing and --no-llm runs."""
    lines = [
        "## Introduction",
        "",
        f"This review examines the hypothesis: *{hypothesis}*. "
        f"It lists {len(papers)} candidate sources selected by metadata heuristics.",
        "",
        "## What the literature says",
        "",
    ]
    for p in papers:
        lines.append(f"- **{p.title}** [@{p.citekey()}] — {p.abstract[:220].strip()}…")
    lines += [
        "",
        "## Assessment of the hypothesis",
        "",
        "_Draft generated without an LLM. Add your synthesis here before publishing._",
        "",
        "## Open questions",
        "",
        "- _List gaps the reviewed work leaves open._",
    ]
    return "\n".join(lines)


def synthesize_review(hypothesis: str, papers: list[Paper], config: AgentConfig) -> str:
    """Produce the literature-review markdown body."""
    if not config.use_llm:
        return _offline_review(hypothesis, papers)

    from .llm import get_chat_model

    model = get_chat_model(config)
    response = model.invoke(
        [("system", SYSTEM_PROMPT), ("human", build_prompt(hypothesis, papers))]
    )
    content = getattr(response, "content", response)
    return content if isinstance(content, str) else str(content)
