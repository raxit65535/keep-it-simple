"""arXiv search via the `arxiv` client library."""

from __future__ import annotations

from ..models import Paper


def search_arxiv(query: str, max_results: int = 30) -> list[Paper]:
    """Search arXiv and return candidate papers.

    Restricted to computer-science categories to match the blog's focus.
    """
    import arxiv

    client = arxiv.Client(page_size=min(max_results, 100), delay_seconds=3, num_retries=3)
    scoped = f"({query}) AND cat:cs.*"
    search = arxiv.Search(
        query=scoped,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers: list[Paper] = []
    for result in client.results(search):
        arxiv_id = result.get_short_id().split("v")[0]
        papers.append(
            Paper(
                title=result.title.strip().replace("\n", " "),
                authors=[a.name for a in result.authors],
                year=result.published.year if result.published else None,
                venue="arXiv",
                abstract=result.summary.strip().replace("\n", " "),
                url=result.entry_id,
                doi=result.doi,
                arxiv_id=arxiv_id,
                source="arxiv",
            )
        )
    return papers
