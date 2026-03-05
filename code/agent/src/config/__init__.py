import os
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseModel):
    url: str
    type: Literal["sse", "streamable_http"]


def _mcp_servers_from_env() -> list[dict]:
    """Read MCP servers from env (MCP_SERVER_1_URL, MCP_SERVER_1_TYPE, ...).
    The operator sets these from the Agent CRD spec.mcpServers."""
    servers = []
    i = 1
    while True:
        url = os.environ.get(f"MCP_SERVER_{i}_URL")
        if not url:
            break
        type_ = os.environ.get(f"MCP_SERVER_{i}_TYPE", "streamable_http")
        servers.append({"url": url.strip(), "type": type_.strip().lower()})
        i += 1
    return servers


class LLMConfig(BaseSettings):
    """Agent config. LLM-related values are read from LLM_* env vars (set by operator from Agent CR spec.llm)."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: Literal["openai", "google", "huggingface", "ollama"] = "openai"
    model_name: str
    base_url: Optional[str] = None
    api_key: str = ""


class AgentConfig(BaseSettings):
    system_prompt: Optional[str] = Field(default=None, validation_alias="SYSTEM_PROMPT")
    mcp_servers: list[MCPServerConfig] = []
    workspace_dir: str = Field(default="/workspace", validation_alias="WORKSPACE_DIR")
    skills_builtin_dir: str = Field(
        default="/skills/builtin", validation_alias="SKILLS_BUILTIN_DIR"
    )
    skills_custom_dir: str = Field(
        default="/skills/custom", validation_alias="SKILLS_CUSTOM_DIR"
    )
    skills_builtins: Optional[str] = Field(
        default=None, validation_alias="SKILLS_BUILTINS"
    )

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v: object) -> list[dict]:
        from_env = _mcp_servers_from_env()
        if from_env:
            return from_env
        if isinstance(v, list):
            return list(v)
        return []


llm_config = LLMConfig()
agent_config = AgentConfig()
