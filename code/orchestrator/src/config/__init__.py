import os
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from shared.logging import get_logger
from shared.llm import LLMConfig  # noqa: F401


logger = get_logger(__name__)


class AgentEndpoint(BaseModel):
    name: str
    url: str
    description: Optional[str] = None


class OrchestratorConfig(BaseSettings):
    orchestrator_name: Optional[str] = Field(
        default=None, validation_alias="ORCHESTRATOR_NAME"
    )
    strategy: str = Field(default="sequence", validation_alias="ORCHESTRATOR_STRATEGY")
    max_rounds: int = Field(default=10, validation_alias="ORCHESTRATOR_MAX_ROUNDS")
    agents: list[AgentEndpoint] = []
    port: int = Field(default=8001, validation_alias="PORT")
    reload: bool = Field(default=False, validation_alias="RELOAD")

    @field_validator("agents", mode="before")
    @classmethod
    def parse_agents(cls, v: object) -> list:
        agents = _agents_from_env()
        if agents:
            return agents
        if isinstance(v, list):
            return list(v)
        return []


class OrchestratorCLIConfig(OrchestratorConfig):
    agent_query: Optional[str] = Field(default=None, validation_alias="AGENT_QUERY")


def _agents_from_env() -> list[dict]:
    """Read agent endpoints from numbered env vars (ORCHESTRATOR_AGENT_1_NAME, _URL, _DESCRIPTION, ...).
    Pydantic-settings can't handle dynamic numbered keys, so we read them explicitly.
    Skips any entry with empty URL (operator must set ORCHESTRATOR_AGENT_*_URL)."""
    agents = []
    i = 1
    while True:
        name = os.environ.get(f"ORCHESTRATOR_AGENT_{i}_NAME")
        if not name:
            break
        url = (os.environ.get(f"ORCHESTRATOR_AGENT_{i}_URL") or "").strip()
        description = os.environ.get(f"ORCHESTRATOR_AGENT_{i}_DESCRIPTION", "")
        if not url:
            logger.warning(
                "Skipping agent %d (%s): ORCHESTRATOR_AGENT_%d_URL is empty",
                i,
                name.strip(),
                i,
            )
        else:
            agents.append(
                {"name": name.strip(), "url": url, "description": description}
            )
        i += 1
    return agents


orchestrator_config = OrchestratorConfig()
