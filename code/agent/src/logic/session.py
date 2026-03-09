from pydantic_ai.messages import ModelResponse


def extract_steps_from_run(result: ModelResponse) -> list[dict]:
    """Build list of {tool, args, result} from the run's new messages (tool calls + returns)."""
    steps: list[dict] = []
    try:
        messages = result.new_messages()
    except Exception:
        return steps
    pending_calls: list[tuple[str, dict]] = []
    for msg in messages:
        parts = getattr(msg, "parts", None) or []
        for part in parts:
            part_type = type(part).__name__
            if "ToolCall" in part_type or "tool_call" in str(part_type):
                pending_calls.append((part.tool, part.args))
            elif "ToolResult" in part_type or "tool_result" in str(part_type):
                tool, args = pending_calls.pop()
                steps.append({"tool": tool, "args": args, "result": part.content})
    return steps
