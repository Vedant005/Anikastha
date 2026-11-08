import pytest

from app.core.config import Settings
from app.review_engine.llm_factory import LLMFactory


def test_llm_factory_gemini():
    settings = Settings(
        LLM_PROVIDER="gemini",
        LLM_MODEL="gemini-2.5-flash",
        GEMINI_API_KEY="test-gemini-key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert "gemini" in model.model.lower()


def test_llm_factory_openai():
    settings = Settings(
        LLM_PROVIDER="openai",
        LLM_MODEL="gpt-4o-mini",
        OPENAI_API_KEY="test-openai-key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert model.model_name == "gpt-4o-mini"


def test_llm_factory_anthropic():
    settings = Settings(
        LLM_PROVIDER="anthropic",
        LLM_MODEL="claude-3-5-sonnet",
        ANTHROPIC_API_KEY="test-anthropic-key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert "claude" in model.model.lower()


def test_llm_factory_groq():
    settings = Settings(
        LLM_PROVIDER="groq",
        LLM_MODEL="llama-3.3-70b-versatile",
        GROQ_API_KEY="gsk_test_groq_key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert model.model_name == "llama-3.3-70b-versatile"
    assert "groq.com" in str(model.openai_api_base)


def test_llm_factory_openrouter():
    settings = Settings(
        LLM_PROVIDER="openrouter",
        LLM_MODEL="meta-llama/llama-3.3-70b-instruct",
        OPENROUTER_API_KEY="sk-or-test-key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert model.model_name == "meta-llama/llama-3.3-70b-instruct"
    assert "openrouter.ai" in str(model.openai_api_base)


def test_llm_factory_huggingface():
    settings = Settings(
        LLM_PROVIDER="huggingface",
        LLM_MODEL="meta-llama/Llama-3-70b-chat-hf",
        HUGGINGFACE_API_KEY="hf_test_key",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert "huggingface.co" in str(model.openai_api_base)


def test_llm_factory_custom():
    settings = Settings(
        LLM_PROVIDER="custom",
        LLM_MODEL="deepseek-coder",
        LLM_BASE_URL="http://localhost:11434/v1",
    )
    model = LLMFactory.get_chat_model(settings=settings)
    assert model is not None
    assert model.model_name == "deepseek-coder"
    assert "11434" in str(model.openai_api_base)


def test_llm_factory_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMFactory.get_chat_model(provider="unsupported_provider")
