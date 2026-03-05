from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from config import llm_config
from logic.prompt import instructions
from logic.tools import assemble_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)

client_kwargs = {}
if llm_config.api_key:
    client_kwargs["api_key"] = llm_config.api_key
if llm_config.base_url:
    client_kwargs["base_url"] = llm_config.base_url

provider = OpenAIProvider(**client_kwargs)


agent = Agent(
    OpenAIChatModel(model_name=llm_config.model_name, provider=provider),
    instructions=instructions(llm_config.system_prompt, llm_config.workspace_dir),
    toolsets=assemble_toolsets(),
)


def agent_loop(query: str) -> str:
    logger.info(f"Agent loop started: {query}")
    res = agent.run_sync(user_prompt=query)
    print(res.all_messages())
    return res.output
