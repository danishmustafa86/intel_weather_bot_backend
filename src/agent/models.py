"""AI model connection with automatic fallback between providers.

The primary provider (PRIMARY_LLM_PROVIDER in .env) is tried first. If its call
fails (bad key, quota exceeded, outage, ...), LangChain's `with_fallbacks`
transparently retries the same request on the next provider that has a key.
"""

import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from src.config import get_settings

logger = logging.getLogger(__name__)

PROVIDER_ORDER = ["gemini", "groq", "xai"]


def _build_gemini() -> BaseChatModel | None:
    s = get_settings()
    if not s.google_api_key:
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=s.gemini_model,
        google_api_key=s.google_api_key,
        temperature=s.llm_temperature,
        max_retries=1,
    )


def _build_groq() -> BaseChatModel | None:
    s = get_settings()
    if not s.groq_api_key:
        return None
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=s.groq_model,
        api_key=s.groq_api_key,
        temperature=s.llm_temperature,
        max_retries=1,
    )


def _build_xai() -> BaseChatModel | None:
    s = get_settings()
    if not s.xai_api_key:
        return None
    from langchain_xai import ChatXAI

    return ChatXAI(
        model=s.xai_model,
        xai_api_key=s.xai_api_key,
        temperature=s.llm_temperature,
        max_retries=1,
    )


BUILDERS = {"gemini": _build_gemini, "groq": _build_groq, "xai": _build_xai}


def get_available_models() -> list[tuple[str, BaseChatModel]]:
    """Return (provider_name, model) pairs, primary provider first."""
    primary = get_settings().primary_llm_provider.lower().strip()
    order = [primary] + [p for p in PROVIDER_ORDER if p != primary]

    models = []
    for name in order:
        builder = BUILDERS.get(name)
        if builder is None:
            continue
        try:
            model = builder()
        except Exception as exc:  # e.g. missing package or invalid config
            logger.warning("Could not initialise %s model: %s", name, exc)
            continue
        if model is not None:
            models.append((name, model))
    return models


def get_llm_with_tools(tools: list[BaseTool]) -> Runnable:
    """Chat model with tools bound, falling back to the next provider on error."""
    models = get_available_models()
    if not models:
        raise RuntimeError(
            "No AI model configured. Add GOOGLE_API_KEY, GROQ_API_KEY or "
            "XAI_API_KEY to backend/.env"
        )

    logger.info("LLM provider order: %s", [name for name, _ in models])
    bound = [model.bind_tools(tools) for _, model in models]
    primary, fallbacks = bound[0], bound[1:]
    return primary.with_fallbacks(fallbacks) if fallbacks else primary
