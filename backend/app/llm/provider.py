from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.config import get_settings


@lru_cache
def get_chat_model() -> BaseChatModel:
    """Returns a LangChain chat model chosen by LLM_PROVIDER.

    Swapping providers (e.g. to OpenAI or Gemini) means adding a branch here and the
    matching `langchain-*` package - every agent node calls this function rather than
    instantiating a provider directly.
    """
    settings = get_settings()

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set; see SETUP.md")
        return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0.2)

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
