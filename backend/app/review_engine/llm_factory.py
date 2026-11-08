import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings, get_settings

logger = logging.getLogger("pr_sentinel.llm_factory")


class LLMFactory:
    """
    Multi-provider LLM Factory supporting:
    - Google Gemini (gemini-2.5-flash, gemini-1.5-pro)
    - OpenAI (gpt-4o, gpt-4o-mini)
    - Anthropic (claude-3-5-sonnet, claude-3-5-haiku)
    - Groq (llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.)
    - OpenRouter (deepseek/deepseek-chat, meta-llama/llama-3.3-70b-instruct, etc.)
    - HuggingFace Inference API (serverless or dedicated endpoints)
    - Custom OpenAI-compatible endpoints (vLLM, Ollama, LocalAI)
    """

    @classmethod
    def get_chat_model(
        cls,
        settings: Settings | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> BaseChatModel:
        cfg = settings or get_settings()
        prov = (provider or cfg.LLM_PROVIDER).lower()
        model = model_name or cfg.LLM_MODEL
        temp = temperature if temperature is not None else cfg.LLM_TEMPERATURE

        logger.info("Initializing LLM client: provider=%s, model=%s", prov, model)

        if prov == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            api_key = cfg.GEMINI_API_KEY or "dummy_key_for_testing"
            if not cfg.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is not set.")
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=temp,
            )

        elif prov == "openai":
            from langchain_openai import ChatOpenAI

            api_key = cfg.OPENAI_API_KEY or "dummy_key_for_testing"
            if not cfg.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY is not set.")
            base_url = cfg.LLM_BASE_URL if cfg.LLM_BASE_URL else None
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=temp,
                base_url=base_url,
            )

        elif prov == "anthropic":
            from langchain_anthropic import ChatAnthropic

            api_key = cfg.ANTHROPIC_API_KEY or "dummy_key_for_testing"
            if not cfg.ANTHROPIC_API_KEY:
                logger.warning("ANTHROPIC_API_KEY is not set.")
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=temp,
            )

        elif prov == "groq":
            from langchain_openai import ChatOpenAI

            api_key = cfg.GROQ_API_KEY or "dummy_key_for_testing"
            if not cfg.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY is not set.")
            base_url = cfg.LLM_BASE_URL or "https://api.groq.com/openai/v1"
            return ChatOpenAI(
                model=model or "llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=temp,
                base_url=base_url,
            )

        elif prov == "openrouter":
            from langchain_openai import ChatOpenAI

            api_key = cfg.OPENROUTER_API_KEY or "dummy_key_for_testing"
            if not cfg.OPENROUTER_API_KEY:
                logger.warning("OPENROUTER_API_KEY is not set.")
            base_url = cfg.LLM_BASE_URL or "https://openrouter.ai/api/v1"
            return ChatOpenAI(
                model=model or "meta-llama/llama-3.3-70b-instruct",
                api_key=api_key,
                temperature=temp,
                base_url=base_url,
            )

        elif prov == "huggingface":
            from langchain_openai import ChatOpenAI

            api_key = cfg.HUGGINGFACE_API_KEY or "dummy_key_for_testing"
            if not cfg.HUGGINGFACE_API_KEY:
                logger.warning("HUGGINGFACE_API_KEY is not set.")
            base_url = cfg.LLM_BASE_URL or "https://api-inference.huggingface.co/v1"
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=temp,
                base_url=base_url,
            )

        elif prov == "custom":
            from langchain_openai import ChatOpenAI

            base_url = cfg.LLM_BASE_URL or "http://localhost:11434/v1"
            api_key = cfg.OPENAI_API_KEY or "not-needed"
            return ChatOpenAI(
                model=model or "llama3",
                api_key=api_key,
                temperature=temp,
                base_url=base_url,
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider '{prov}'. "
                "Supported options: gemini, openai, anthropic, groq, openrouter, huggingface, custom"
            )
