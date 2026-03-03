from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from config import llm_config
from logic.prompt import instructions
from logic.tools import get_tools

client_kwargs = {}
if llm_config.api_key:
    client_kwargs["api_key"] = llm_config.api_key
if llm_config.base_url:
    client_kwargs["base_url"] = llm_config.base_url

provider = OpenAIProvider(**client_kwargs)


def _mcp_toolsets():
    toolsets = []
    for s in llm_config.mcp_servers:
        if s.type == "sse":
            toolsets.append(MCPServerSSE(s.url))
        elif s.type == "streamable_http":
            toolsets.append(MCPServerStreamableHTTP(s.url))
    return toolsets


_workspace_toolset = FunctionToolset(tools=get_tools())

agent = Agent(
    OpenAIChatModel(model_name=llm_config.model_name, provider=provider),
    instructions=instructions(llm_config.system_prompt, llm_config.workspace_dir),
    toolsets=[_workspace_toolset, *_mcp_toolsets()],
)


def agent_loop(query: str) -> str:
    res = agent.run_sync(user_prompt=query)
    print(res.all_messages())
    return res.output
