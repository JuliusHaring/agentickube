import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from shared.llm import LLMConfig  # noqa: F401 (re-exported for backward compat)


class MCPServerConfig(BaseModel):
    url: str
    type: str


class AgentConfig(BaseSettings):
    agent_name: str | None = Field(default=None, validation_alias="AGENT_NAME")
    system_prompt: str | None = Field(default=None, validation_alias="SYSTEM_PROMPT")
    mcp_servers: list[MCPServerConfig] = []
    workspace_dir: str = Field(default="/workspace", validation_alias="WORKSPACE_DIR")
    conversation_memory_enabled: bool = Field(
        default=False, validation_alias="CONVERSATION_MEMORY_ENABLED"
    )
    conversation_max_history: int = Field(
        default=20, validation_alias="CONVERSATION_MAX_HISTORY"
    )
    port: int = Field(default=8000, validation_alias="PORT")
    reload: bool = Field(default=False, validation_alias="RELOAD")

    @property
    def skills_dir(self) -> str:
        """Runtime skills directory — always inside the workspace."""
        return str(Path(self.workspace_dir) / "skills")

    builtin_skills: list[str] | None = Field(
        default=None, validation_alias="BUILTIN_SKILLS"
    )

    @field_validator("builtin_skills", mode="before")
    @classmethod
    def parse_builtin_skills(cls, v: object) -> list[str] | None:
        if v is None:
            return None
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            s = v.strip()
            # Empty string means explicit empty allowlist (no skills).
            if not s:
                return []
            return [x.strip() for x in s.split(",") if x.strip()]
        return None

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v: object) -> list:
        servers = _mcp_servers_from_env()
        if servers:
            return servers
        if isinstance(v, list):
            return list(v)
        return []


class AgentCLIConfig(AgentConfig):
    agent_query: str | None = Field(default=None, validation_alias="AGENT_QUERY")


def _mcp_servers_from_env() -> list[dict]:
    """Read MCP servers from numbered env vars (MCP_SERVER_1_URL, MCP_SERVER_1_TYPE, ...).
    Pydantic-settings can't handle dynamic numbered keys, so we read them explicitly."""
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


llm_config = LLMConfig()  # type: ignore - managed by pydantic settings
agent_config = AgentConfig()
