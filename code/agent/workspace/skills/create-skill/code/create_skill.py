import os
from pathlib import Path
from textwrap import dedent
from typing import Dict, Literal, Optional

from config import agent_config  # type:ignore[unresolved-import]


def _normalize_skill_name(name: str) -> str:
    """Normalize a proposed skill name to lowercase-hyphen format."""
    name = name.strip().lower().replace(" ", "-")
    # keep only lowercase letters, digits, and hyphens
    safe = []
    for ch in name:
        if ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "-":
            safe.append(ch)
    normalized = "".join(safe).strip("-")
    if not normalized:
        return "Skill name is empty after normalization."
    if len(normalized) > 64:
        return "Skill name must be at most 64 characters."
    return normalized


def _ensure_under_skills(root: Path, target: Path) -> str | None:
    """
    Ensure that `target` is inside `root` (prevent escaping via '..', symlinks, etc.).
    """
    root = root.resolve()
    target = target.resolve()
    if root not in target.parents and root != target:
        return f"Refusing to write outside skills root: {target.resolve()}"


def skill_exists(skill_name: str, skills_root: str = agent_config.skills_dir) -> bool:
    """
    Check whether a skill already exists under the skills root.

    Args:
        skill_name: Logical name (will be normalized to lowercase-hyphen).
        skills_root: Root directory where skills are stored (default from config).

    Returns:
        True if the skill directory exists (and contains SKILL.md), False otherwise.
    """
    try:
        normalized_name = _normalize_skill_name(skill_name)
    except ValueError:
        return False
    skill_dir = Path(skills_root) / normalized_name
    return skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()


def create_skill(
    skill_name: str,
    description: str = "",
    title: Optional[str] = None,
    instructions: str = "",
    code_files: Optional[Dict[str, str]] = None,
    skills_root: str = agent_config.skills_dir,
    if_exists: Literal["error", "skip", "overwrite"] = "skip",
) -> str:
    """
    Create a new skill under the skills/ folder.

    This function ONLY writes files under the given `skills_root` directory.
    It does not run subprocesses, install packages, or touch anything else.

    Args:
        skill_name: Logical name for the skill (will be normalized to lowercase-hyphen).
        description: One-line description for SKILL.md frontmatter (optional; default from skill name if empty).
        title: Optional human-readable title (defaults to skill_name).
        instructions: Markdown body content for SKILL.md.
        code_files: Optional mapping of relative python file names under `code/`
                    (e.g. {"tool.py": "def my_tool(...): ..."}).
        skills_root: Root directory where skills are stored (default "skills").
        if_exists: When the skill directory already exists: "skip" (return existing path; default),
                   "error" (return error message), or "overwrite" (update SKILL.md and code_files).

    Returns:
        The absolute path to the created or existing skill directory.

    """
    normalized_name = _normalize_skill_name(skill_name)
    description = (description or "").strip()
    if not description:
        description = f"User-defined skill: {normalized_name}."
    if len(description) > 1024:
        return "Description must be <= 1024 characters."

    skills_root_path = Path(skills_root)
    skills_root_path.mkdir(parents=True, exist_ok=True)

    skill_dir = skills_root_path / normalized_name
    _ensure_under_skills(skills_root_path, skill_dir)

    if skill_dir.exists():
        if if_exists == "error":
            return f"Skill directory already exists: {skill_dir.resolve()}"
        if if_exists == "skip":
            return str(skill_dir.resolve())
        # overwrite: fall through and write SKILL.md / code_files

    instructions_blank = not (instructions or "").strip()
    if description == f"User-defined skill: {normalized_name}." and instructions_blank:
        return (
            "Stub skills are not allowed: provide a real description and instructions "
            "(and code_files if the skill needs tools)."
        )

    desc_lower = description.lower()
    tool_phrases = (
        "takes a ",
        "takes an ",
        " returns ",
        "the function ",
        " library",
        "requires the ",
    )
    has_tool_language = any(p in desc_lower for p in tool_phrases)
    no_code = not code_files
    if has_tool_language and no_code:
        return (
            "Description describes a callable tool but no code_files provided. "
            "Add code_files with the Python implementation."
        )

    skill_dir.mkdir(parents=False, exist_ok=True)

    title = title or normalized_name
    skill_md_path = skill_dir / "SKILL.md"
    _ensure_under_skills(skills_root_path, skill_md_path)

    skill_md_content = (
        dedent(
            f"""\
        ---
        name: {normalized_name}
        description: {description}
        ---

        # {title}

        {instructions.strip()}
        """
        ).rstrip()
        + "\n"
    )

    skill_md_path.write_text(skill_md_content, encoding="utf-8")

    # Optional code files, always under skills/<skill-name>/code/
    if code_files:
        code_dir = skill_dir / "code"
        _ensure_under_skills(skills_root_path, code_dir)
        code_dir.mkdir(parents=False, exist_ok=True)

        for rel_name, source in code_files.items():
            rel_name = rel_name.strip()
            if not rel_name:
                return "Code file name cannot be empty."
            if os.path.isabs(rel_name):
                return "Code file name must be relative, not absolute."
            if ".." in Path(rel_name).parts:
                return "Code file name cannot contain '..' components."

            file_path = code_dir / rel_name
            _ensure_under_skills(skills_root_path, file_path)

            if file_path.suffix != ".py":
                return f"Code file must have .py extension: {rel_name}"

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(source, encoding="utf-8")

    return str(skill_dir.resolve())
