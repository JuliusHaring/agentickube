---
name: create-skill
description: Create new agent skills (SKILL.md files with optional code/ tools) for this agentickube agent. Use when the user asks to create, write, or define a new skill, or asks about skill structure, format, or best practices.
---

# Creating Skills

When the user asks you to create a skill, you MUST write it to disk immediately using your workspace file tools. Do NOT just display the content or explain how to deploy it.

All actions for this skill are **strictly limited to file writes under the `skills/` folder tree** and must only produce plain Python or Markdown.

- You MUST NOT create, edit, or delete files outside `skills/`.
- You MUST NOT use `subprocess`, shell commands, package managers, or any external tools.
- You MUST NOT install dependencies, modify environment/system configuration, or perform any network or OS-level side effects.
- You SHOULD keep generated Python simple and importable (no CLIs, servers, or long-running processes) and keep SKILL.md content concise.

## Workflow

1. Create `skills/<skill-name>/SKILL.md` in your workspace using your file write tool.
2. If the skill needs executable tools, also create `skills/<skill-name>/code/<tool>.py`.
3. Confirm to the user: the file path(s) and a one-line summary.

**Do not create stub skills.** Every skill MUST have a real, specific `description` and substantive `instructions`. **If the skill describes a callable tool** (e.g. "takes a ticker", "returns price", "uses library X", "the function") **you MUST pass `code_files`** with the actual Python. Never write a description that promises a function or tool without adding the corresponding `code_files`—a skill with only SKILL.md and no `code/` when the description describes a tool is wrong and useless.

That's it. Write the files under `skills/` and nothing else. Don't explain Kubernetes, ConfigMaps, or YAML configuration.

## How to use the `create_skill` and `skill_exists` tools

**Prefer calling the `create_skill` tool** instead of writing SKILL.md and code files by hand. It enforces layout, frontmatter, and path safety. Always pass a concrete `description` and `instructions`. **If the description or user request describes a tool, function, or data-fetch (e.g. fetch stocks, get price, call API), you MUST pass `code_files`** with real Python—never create only SKILL.md when the skill is supposed to expose a callable tool.

**Check first (optional):** `skill_exists(skill_name, skills_root?)` returns `True` if a skill with that name already exists (normalized name, and `SKILL.md` present), else `False`. Use it to avoid overwriting or to choose `if_exists`.

**create_skill** — call with:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `skill_name` | Yes | Logical name (e.g. "my-skill"); normalized to lowercase-hyphen, max 64 chars. |
| `description` | No | One-line for frontmatter; if empty, a default is used. Max 1024 chars. |
| `title` | No | Human-readable title in SKILL.md; defaults to normalized skill name. |
| `instructions` | No | Markdown body for SKILL.md (the main instructions to the agent). |
| `code_files` | No | Dict of `filename -> full Python source`, e.g. `{"my_tool.py": "def my_tool(x: int) -> str: ..."}`. Files go under `code/`; only `.py` allowed. |
| `skills_root` | No | Root directory for skills (default from config, usually `skills`). |
| `if_exists` | No | When the skill dir already exists: `"skip"` (return path, do nothing; default), `"error"` (raise FileExistsError), or `"overwrite"` (update SKILL.md and code_files). |

**Returns:** Absolute path to the created (or existing, if `if_exists="skip"`) skill directory.

**Example:** To create a skill with one tool:

```text
create_skill(
  skill_name="greet",
  description="Replies with a greeting. Use when the user says hello or asks for a greeting.",
  title="Greet",
  instructions="When using the greet tool, keep the message short and friendly.",
  code_files={
    "greet.py": 'def greet(name: str = "world") -> str:\n    """Say hello to the given name."""\n    return f"Hello, {name}!"\n'
  }
)
```

If the skill already exists, the default `if_exists="skip"` returns its path without changing anything. Use `if_exists="overwrite"` to update SKILL.md and code_files, or `if_exists="error"` to raise `FileExistsError`. All writes stay under `skills_root`; no subprocess or installs.

**New skill tools and this session:** Tools from a skill you just created (in `code_files`) are **not** loaded in the current session; they are loaded at agent startup. Tell the user that the new tool(s) will be available after the agent or deployment restarts. Do not say you "cannot execute" the new tool because of "available tools"—explain that it will be available after restart.

## Skill Directory Layout

```
skills/<skill-name>/
  SKILL.md              # required: prompt injected into system instructions
  code/                 # optional: Python tool functions
    <tool>.py          # public functions become agent tools automatically
```

## SKILL.md Format

```markdown
---
name: skill-name
description: What this skill does and when to use it. Be specific.
---

# Skill Title

Instructions for the agent.
```

### Frontmatter

| Field | Required | Rules |
|---|---|---|
| `name` | Yes | Lowercase, hyphens only, max 64 chars |
| `description` | Yes | Max 1024 chars; WHAT it does + WHEN to use it |

Description formula: "[What it does]. [Key capabilities]. Use when [trigger conditions]."
Write in third person. Include terms the user would actually type.

## Code Tools (code/*.py)

Each `.py` file in `code/` is auto-imported. All top-level functions whose names do NOT start with `_` are registered as tools the agent can call.

Rules for tool functions:
- The function **docstring** is what the LLM sees as the tool description. Make it clear and concise.
- Use **type hints** on all parameters so the LLM knows the expected types.
- Functions starting with `_` are private helpers, not exposed as tools.
- Any packages installed in the agent image are available to import, but you MUST NOT install new packages or invoke external processes from these tools.

Example (`code/dice.py`):
```python
import random

def roll_dice(sides: int = 6, count: int = 1) -> str:
    """Roll dice and return the results.

    Args:
        sides: Number of sides per die (default 6).
        count: Number of dice to roll (default 1).
    """
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    if count == 1:
        return f"Rolled a d{sides}: {total}"
    return f"Rolled {count}d{sides}: {', '.join(map(str, rolls))} (total: {total})"
```

## Authoring Principles

- **Be concise.** The agent already knows common concepts. Only add knowledge it lacks. Keep SKILL.md under 500 lines.
- **Match specificity to fragility.** Creative tasks get loose guidance. Fragile operations get exact commands.
- **Progressive disclosure.** Essentials in SKILL.md, details in separate reference files read on demand.

## Anti-Patterns

- Verbose explanations of things the agent already knows
- Multiple tool options without a clear default
- Vague names like `helper`, `utils`, `misc`
- Inconsistent terminology
