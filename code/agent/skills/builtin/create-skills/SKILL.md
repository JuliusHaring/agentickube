---
name: create-skills
description: Create new agent skills (SKILL.md files with optional code/ tools) for this agentickube agent. Use when the user asks to create, write, or define a new skill, or asks about skill structure, format, or best practices.
---

# Creating Skills

When the user asks you to create a skill, you MUST write it to disk immediately using your workspace file tools. Do NOT just display the content or explain how to deploy it.

## Workflow

1. Create `skills/custom/<skill-name>/SKILL.md` in your workspace using your file write tool.
2. If the skill needs executable tools, also create `skills/custom/<skill-name>/code/<tool>.py`.
3. Confirm to the user: the file path(s) and a one-line summary.

That's it. Write the files. Don't explain Kubernetes, ConfigMaps, or YAML configuration.

## Skill Directory Layout

```
skills/code/<skill-name>/
  SKILL.md              # required: prompt injected into system instructions
  code/                 # optional: Python tool functions
    my_tool.py          # public functions become agent tools automatically
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
- Any packages installed in the agent image are available to import.

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
