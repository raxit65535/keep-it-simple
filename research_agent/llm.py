"""LLM provider abstraction: local (Ollama) or cloud (OpenAI)."""

from __future__ import annotations

from .config import AgentConfig


class LLMUnavailableError(RuntimeError):
    """Raised when the requested LLM provider cannot be initialised."""


def get_chat_model(config: AgentConfig):
    """Return a LangChain chat model for the configured provider.

    Imports are lazy so the rest of the pipeline works without the LLM extras
    installed (e.g. offline `--no-llm` runs).
    """
    provider = config.provider.lower()
    model = config.default_model()

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise LLMUnavailableError(
                "langchain-ollama is not installed. Run `uv sync --group agent`."
            ) from exc
        return ChatOllama(model=model, temperature=config.temperature)

    if provider == "openai":
        import os

        if not os.environ.get("OPENAI_API_KEY"):
            raise LLMUnavailableError("OPENAI_API_KEY is not set but provider is 'openai'.")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise LLMUnavailableError(
                "langchain-openai is not installed. Run `uv sync --group agent`."
            ) from exc
        return ChatOpenAI(model=model, temperature=config.temperature)

    raise LLMUnavailableError(f"Unknown LLM provider: {config.provider!r}")
