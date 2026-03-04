def instructions(system_prompt: str | None, workspace_dir: str = "/workspace") -> str:
    prompt = (
        """
ALWAYS USE THE TOOLS / MCP SERVERS IN EVERY QUERY BY THE USER!

You have tools for the workspace: listing, reading, and writing files. Use them for any file-related request. Paths are relative to the workspace root """
        + workspace_dir
        + """.
"""
    )

    if system_prompt:
        prompt += f"""Follow the system prompt given by the user:
---
{system_prompt}
---"""
    return prompt
