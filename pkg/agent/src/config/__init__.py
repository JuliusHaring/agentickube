import os
from typing import Literal, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


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
    model_name: str
    base_url: Optional[str] = None
    api_key: str = ""
    system_prompt: Optional[str] = None
    mcp_servers: list[MCPServerConfig] = []

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
