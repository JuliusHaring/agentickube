"""Shared LLM configuration and provider selection.

Used by both the agent and orchestrator images.
"""

from typing import Literal

from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.huggingface import HuggingFaceProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.logging import get_logger

logger = get_logger(__name__)

PROVIDER_MAP = {
    "openai": (OpenAIProvider, OpenAIChatModel),
    "google": (GoogleProvider, GoogleModel),
    "huggingface": (HuggingFaceProvider, OpenAIChatModel),
    "ollama": (OllamaProvider, OpenAIChatModel),
}


class LLMConfig(BaseSettings):
    """LLM-related values read from LLM_* env vars (set by operator from CR spec.llm)."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: Literal["openai", "google", "huggingface", "ollama"] = "openai"
    model_name: str
    base_url: str | None = None
    api_key: str = ""


def get_model(config: LLMConfig | None = None) -> Model:
    config = config or LLMConfig()  # type: ignore - managed by pydantic settings
    provider_cls, model_cls = PROVIDER_MAP[config.provider]

    client_kwargs = {}
    if config.api_key:
        client_kwargs["api_key"] = config.api_key
    if config.base_url:
        client_kwargs["base_url"] = config.base_url

    provider = provider_cls(**client_kwargs)
    model = model_cls(model_name=config.model_name, provider=provider)  # type: ignore

    logger.info(f"Using provider: {provider}")

    return model
