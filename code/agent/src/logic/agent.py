from pydantic_ai import Agent
from logic.providers import get_provider
from pydantic_ai.models.openai import OpenAIChatModel
from config import llm_config
from logic.prompt import instructions
from logic.tools import assemble_toolsets
from shared.logging import get_logger

logger = get_logger(__name__)


provider = get_provider()


agent = Agent(
    model=OpenAIChatModel(model_name=llm_config.model_name, provider=provider),
    instructions=instructions(llm_config.system_prompt, llm_config.workspace_dir),
    toolsets=assemble_toolsets(),
)


def agent_loop(query: str) -> str:
    logger.info(f"Agent loop started: {query}")
    res = agent.run_sync(user_prompt=query)
    print(res.all_messages())
    return res.output
