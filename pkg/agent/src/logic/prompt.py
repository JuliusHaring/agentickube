def instructions(system_prompt: str) -> str:
    prompt = """
ALWAYS USE THE TOOLS / MCP SERVERS IN EVERY QUERY BY THE USER!
"""

    if system_prompt is not None:
        prompt += f"""Follow the system prompt given by the user:
---
{system_prompt}
---"""
