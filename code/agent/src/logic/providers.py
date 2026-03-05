from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.huggingface import HuggingFaceProvider
from pydantic_ai.providers.ollama import OllamaProvider

from config import llm_config
from shared.logging import get_logger

logger = get_logger(__name__)

PROVIDER_MAP = {
    "openai": (OpenAIProvider, OpenAIChatModel),
    "google": (GoogleProvider, GoogleModel),
    "huggingface": (HuggingFaceProvider, OpenAIChatModel),
    "ollama": (OllamaProvider, OpenAIChatModel),
}


def get_model() -> Model:
    provider_cls, model_cls = PROVIDER_MAP[llm_config.provider]

    client_kwargs = {}
    if llm_config.api_key:
        client_kwargs["api_key"] = llm_config.api_key
    if llm_config.base_url:
        client_kwargs["base_url"] = llm_config.base_url

    provider = provider_cls(**client_kwargs)
    model = model_cls(model_name=llm_config.model_name, provider=provider)

    logger.info(f"Using provider: {provider}")

    return model
