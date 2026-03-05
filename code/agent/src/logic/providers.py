from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.huggingface import HuggingFaceProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers import Provider

from config import llm_config
from shared.logging import get_logger

logger = get_logger(__name__)


def get_provider() -> Provider:
    provider = llm_config.provider
    provider_map = {
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "huggingface": HuggingFaceProvider,
        "ollama": OllamaProvider,
    }

    logger.info(f"Using provider: {provider}")

    client_kwargs = {}
    if llm_config.api_key:
        client_kwargs["api_key"] = llm_config.api_key
    if llm_config.base_url:
        client_kwargs["base_url"] = llm_config.base_url

    provider_instance = provider_map[provider](**client_kwargs)

    return provider_instance
