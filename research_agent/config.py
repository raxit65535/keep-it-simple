"""Runtime configuration for the research agent (env-overridable)."""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / ".agent" / "runs"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


@dataclass
class AgentConfig:
    """All knobs for a single research run.

    LLM provider is pluggable: "ollama" (fully local) or "openai" (cloud API).
    Selected via KIS_LLM_PROVIDER or the --provider CLI flag.
    """

    provider: str = field(default_factory=lambda: os.environ.get("KIS_LLM_PROVIDER", "ollama"))
    model: str = field(default_factory=lambda: os.environ.get("KIS_LLM_MODEL", ""))
    temperature: float = 0.2

    # Retrieval / screening.
    max_candidates: int = field(default_factory=lambda: _env_int("KIS_MAX_CANDIDATES", 30))
    keep_top_k: int = field(default_factory=lambda: _env_int("KIS_KEEP_TOP_K", 8))
    min_citations: int = field(default_factory=lambda: _env_int("KIS_MIN_CITATIONS", 5))
    recency_years: int = field(default_factory=lambda: _env_int("KIS_RECENCY_YEARS", 8))
    min_credibility: float = 0.45

    use_llm: bool = True

    def default_model(self) -> str:
        if self.model:
            return self.model
        return "llama3.1" if self.provider == "ollama" else "gpt-4o-mini"

    def current_year(self) -> int:
        return _dt.date.today().year
