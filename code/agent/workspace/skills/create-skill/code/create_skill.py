"""
Create agent skills under a skills root. Uses only the Python standard library.
Enforces: correct location, valid name and description, no subprocess.
Raises on invalid input or when creation cannot be completed.
"""

import re
from pathlib import Path

from config import agent_config  # type:ignore[unresolved-import]

SKILL_MD = "SKILL.md"
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
NAME_MAX_LEN = 64
DESCRIPTION_MAX_LEN = 1024


def _validate_skill_name(name: str) -> None:
    """Raise ValueError if skill name is invalid."""
    if not name or not isinstance(name, str):
        raise ValueError("Skill name must be a non-empty string")
    n = name.strip()
    if len(n) > NAME_MAX_LEN:
        raise ValueError(f"Skill name must be at most {NAME_MAX_LEN} characters")
    if not NAME_PATTERN.match(n):
        raise ValueError(
            "Skill name must be lowercase letters, numbers, and hyphens only "
            "(e.g. my-skill, parse-csv)"
        )


def _validate_description(description: str) -> None:
    """Raise ValueError if description is invalid."""
    if not isinstance(description, str):
        raise ValueError("Description must be a string")
    d = description.strip()
    if not d:
        raise ValueError("Description must be non-empty")
    if len(d) > DESCRIPTION_MAX_LEN:
        raise ValueError(
            f"Description must be at most {DESCRIPTION_MAX_LEN} characters"
        )


def _skill_dir(skills_root: str, skill_name: str) -> Path:
    """Resolve skill directory; raise ValueError if path escapes skills root."""
    root = Path(skills_root).resolve()
    if not root.is_dir():
        raise OSError(f"Skills root is not a directory: {root}")
    # Ensure skill_name has no path components (no slashes, no parent traversal)
    safe_name = skill_name.strip()
    if re.search(r"[/\\]|\.\.", safe_name):
        raise ValueError("Skill name must not contain path separators or '..'")
    skill_path = (root / safe_name).resolve()
    try:
        skill_path.relative_to(root)
    except ValueError:
        raise ValueError(f"Skill path would escape skills root: {skill_path}")
    return skill_path


def check_skill_exists(skill_name: str, skills_root: str | None = None) -> bool:
    """Return True if a skill directory exists under skills_root and contains SKILL.md.

    Args:
        skill_name: Directory name of the skill (must match name rules).
        skills_root: Root directory under which skills live. Defaults to agent_config.skills_dir.

    Returns:
        True if the skill directory exists and has a SKILL.md file.

    Raises:
        ValueError: If skill_name is invalid.
        OSError: If skills_root is not a directory.
    """
    root = skills_root if skills_root is not None else agent_config.skills_dir
    _validate_skill_name(skill_name)
    path = _skill_dir(root, skill_name)
    return path.is_dir() and (path / SKILL_MD).is_file()


def create_skill(
    skill_name: str,
    description: str,
    body_md: str = "",
    skills_root: str | None = None,
) -> Path:
    """Create a new skill directory with SKILL.md and a code/ subdirectory. Does not use subprocess.
    Requires both skill_name and description. Creates scaffold only; add implementation in code/ using requests or httpx.

    Args:
        skill_name: Directory name (and frontmatter name); must be valid.
        description: Frontmatter description (required); must be non-empty, max 1024 chars.
        body_md: Optional markdown body for SKILL.md (default minimal heading).
        skills_root: Root directory under which to create the skill. Defaults to agent_config.skills_dir.

    Returns:
        Path to the created skill directory (contains SKILL.md and code/).

    Raises:
        ValueError: If name or description is invalid.
        FileExistsError: If the skill directory already exists.
        OSError: If skills_root is invalid or creation fails.
    """
    root = skills_root if skills_root is not None else agent_config.skills_dir
    _validate_skill_name(skill_name)
    _validate_description(description)
    path = _skill_dir(root, skill_name)

    if path.exists():
        raise FileExistsError(f"Skill already exists: {path}")

    # Escape optional YAML in description for frontmatter (simple: no multi-line)
    desc_escaped = description.strip().replace("\n", " ").replace('"', '\\"')

    content = f"""---
name: {skill_name.strip()}
description: {desc_escaped}
---

# {skill_name.strip().replace("-", " ").title()}

{body_md.strip() or "Instructions and examples go here."}
"""

    code_dir = path / "code"

    try:
        path.mkdir(parents=True, exist_ok=False)
        code_dir.mkdir(parents=False, exist_ok=False)
        (path / SKILL_MD).write_text(content, encoding="utf-8")
    except OSError as e:
        raise OSError(f"Cannot create skill at {path}: {e}") from e

    return path
