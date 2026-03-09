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
                tool = getattr(part, "tool_name", None) or getattr(part, "tool", None)
                args = getattr(part, "args_as_dict", None)
                if callable(args):
                    args = args()
                else:
                    args = getattr(part, "args", None)
                if tool is not None:
                    pending_calls.append((tool, args if args is not None else {}))
            elif (
                "ToolResult" in part_type
                or "tool_result" in part_type
                or "ToolReturn" in part_type
                or "tool_return" in part_type
            ):
                if pending_calls:
                    tool, args = pending_calls.pop()
                    content = getattr(part, "content", None)
                    steps.append({"tool": tool, "args": args, "result": content})
    return steps
