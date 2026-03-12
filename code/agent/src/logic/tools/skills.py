"""Skill discovery, metadata loading, and script execution (Anthropic SKILL.md spec)."""

import re
import shutil
import subprocess
import sys
from pydantic import BaseModel
from pathlib import Path

import yaml

from shared.logging import get_logger
from config import agent_config

logger = get_logger(__name__)

SCRIPT_TIMEOUT_SECONDS = 60


class SkillMetadata(BaseModel):
    name: str
    description: str
    dir_name: str


def _discover_skill_dirs(directory: str) -> dict[str, Path]:
    """Discover skill directories (subdirs that contain SKILL.md). Returns {dir_name: skill_dir}."""
    root = Path(directory)
    logger.info(f"Discovering skills in {root}")
    if not root.is_dir():
        return {}
    dirs: dict[str, Path] = {}
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            dirs[child.name] = child
    return dirs


def _filtered_skill_dirs() -> dict[str, Path]:
    """Discover skill dirs with builtin_skills allowlist applied."""
    found = _discover_skill_dirs(agent_config.skills_dir)
    if agent_config.builtin_skills is not None:
        found = {k: v for k, v in found.items() if k in agent_config.builtin_skills}
    return found


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _parse_skill_frontmatter(path: Path, dir_name: str) -> SkillMetadata | None:
    """Parse YAML frontmatter from a SKILL.md file. Returns None on missing/invalid."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to read %s: %s", path, e)
        return None

    m = _FRONTMATTER_RE.match(text)
    if not m:
        logger.warning("No YAML frontmatter in %s", path)
        return None

    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        logger.warning("Invalid YAML frontmatter in %s: %s", path, e)
        return None

    if not isinstance(data, dict):
        logger.warning("Frontmatter is not a mapping in %s", path)
        return None

    name = data.get("name")
    description = data.get("description")
    if not name or not description:
        logger.warning("Missing name or description in %s", path)
        return None

    return SkillMetadata(
        name=str(name), description=str(description), dir_name=dir_name
    )


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from SKILL.md content, returning only the body."""
    m = _FRONTMATTER_RE.match(text)
    if m:
        return text[m.end() :]
    return text


def load_skill_metadata() -> list[SkillMetadata]:
    """Load metadata (name + description) from all discovered skills."""
    found = _filtered_skill_dirs()
    results: list[SkillMetadata] = []
    for dir_name, skill_dir in found.items():
        meta = _parse_skill_frontmatter(skill_dir / "SKILL.md", dir_name)
        if meta:
            logger.info("Loaded skill metadata: %s (%s)", meta.name, dir_name)
            results.append(meta)
        else:
            logger.warning("Skipping skill %s (no valid frontmatter)", dir_name)
    return results


def list_skills() -> str:
    """Return available skills. Use the exact skill_id (dir name) in get_skill_instructions and run_skill_script.

    Returns a line-per-skill list: skill_id — description
    """
    meta_list = load_skill_metadata()
    if not meta_list:
        return "No skills available."
    lines = [f"{s.dir_name} — {s.description}" for s in meta_list]
    return (
        "Available skills (use these exact skill_id values in other tools):\n"
        + "\n".join(lines)
    )


def get_skill_instructions(skill_name: str) -> str:
    """Load full instructions (markdown body, frontmatter stripped) for a skill.

    Args:
        skill_name: The directory name of the skill (e.g. 'internet', 'markdown').
    """
    found = _filtered_skill_dirs()
    skill_dir = found.get(skill_name)
    if skill_dir is None:
        available = ", ".join(sorted(found.keys())) or "(none)"
        logger.error(
            "Skill '%s' not found. Available skills: %s", skill_name, available
        )
        raise ValueError(
            f"Skill '{skill_name}' not found. Available skills: {available}"
        )

    path = skill_dir / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Error reading SKILL.md for '%s': %s", skill_name, e)
        raise ValueError(f"Error reading SKILL.md for '{skill_name}': {e}")

    return _strip_frontmatter(text).strip()


def _looks_like_script_filename(s: str) -> bool:
    return bool(s) and ("." in s) and s.split(".")[-1].lower() in ("py", "sh")


def run_skill_script(
    skill_name: str,
    script_name: str,
    arguments: list[str] | None = None,
) -> str:
    """Run a script from a skill's scripts/ directory and return its output.

    Args:
        skill_name: The directory name of the skill (e.g. 'internet', 'markdown').
        script_name: Filename of the script inside the skill's scripts/ dir (e.g. 'fetch_url.py').
        arguments: Optional list of command-line arguments to pass to the script.
    """
    logger.info(f"Running skill script: {skill_name}, {script_name}, {arguments}")
    found = _filtered_skill_dirs()
    skill_dir = found.get(skill_name)

    # Model sometimes passes (script_name, first_arg, ...) omitting skill_name; resolve skill from script.
    if skill_dir is None and _looks_like_script_filename(skill_name):
        for sid, sdir in found.items():
            scripts_dir = sdir / "scripts"
            if scripts_dir.is_dir() and (scripts_dir / skill_name).is_file():
                arguments = (
                    [script_name]
                    if arguments is None
                    else [script_name]
                    + (list(arguments) if isinstance(arguments, list) else [arguments])
                )
                script_name = skill_name
                skill_name = sid
                skill_dir = sdir
                break

    if skill_dir is None:
        available = ", ".join(sorted(found.keys())) or "(none)"
        logger.error(
            "Skill '%s' not found. Available skills: %s", skill_name, available
        )
        raise ValueError(
            f"Skill '{skill_name}' not found. Available skills: {available}"
        )

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        logger.error("Skill '%s' has no scripts/ directory.", skill_name)
        raise ValueError(f"Skill '{skill_name}' has no scripts/ directory.")

    script_path = (scripts_dir / script_name).resolve()
    if not script_path.is_relative_to(scripts_dir.resolve()):
        return "Error: script path must stay inside scripts/ (no path traversal)."
    if not script_path.is_file():
        available_scripts = [
            f.name for f in sorted(scripts_dir.iterdir()) if f.is_file()
        ]
        logger.error(
            "Script '%s' not found in %s/scripts/. Available scripts: %s",
            script_name,
            skill_name,
            available_scripts,
        )
        raise ValueError(
            f"Script '{script_name}' not found in {skill_name}/scripts/. Available scripts: {available_scripts}"
        )

    suffix = script_path.suffix.lower()
    if suffix == ".py":
        cmd = [sys.executable, str(script_path)]
    elif suffix == ".sh":
        cmd = ["bash", str(script_path)]
    else:
        logger.error(
            "Unsupported script type '%s'. Only .py and .sh are supported.", suffix
        )
        raise ValueError(
            f"Unsupported script type '{suffix}'. Only .py and .sh are supported."
        )

    # Normalize: model may pass a single string as third positional; always pass list of args.
    if arguments is not None:
        if isinstance(arguments, str):
            args_list = [arguments]
        else:
            args_list = [str(a) for a in arguments]

        # Strip one level of surrounding quotes so "'https://...'" becomes "https://..."
        def unquote(s: str) -> str:
            s = s.strip()
            if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
                return s[1:-1]
            return s

        cmd.extend(unquote(a) for a in args_list)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            cwd=str(scripts_dir),
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        logger.error(
            "Script '%s' timed out after %s seconds.",
            script_name,
            SCRIPT_TIMEOUT_SECONDS,
        )
        raise ValueError(
            f"Script '{script_name}' timed out after {SCRIPT_TIMEOUT_SECONDS} seconds."
        )
    except Exception as e:
        logger.error("Error running script '%s': %s", script_name, e)
        raise ValueError(f"Error running script '{script_name}': {e}")


WORKSPACE_TEMPLATE_DIR = "/code/workspace"


def sync_workspace_from_repo(
    template_dir: str = WORKSPACE_TEMPLATE_DIR,
    workspace_dir: str = agent_config.workspace_dir,
) -> None:
    """Sync repo workspace template into the runtime workspace, then apply builtin_skills.

    Copies the full template (skills and any future content) into workspace_dir so
    a PVC mount gets prefilled. If builtin_skills is set, only those skill dirs are
    kept in workspace/skills/; all others are removed.
    """
    template = Path(template_dir)
    workspace = Path(workspace_dir)

    logger.info(f"Syncing workspace from {template_dir} into {workspace_dir}")
    if not template.is_dir():
        logger.warning("No workspace template at %s, skipping sync", template_dir)
        return

    logger.info(f"Creating workspace directory: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)

    logger.info(f"Copying workspace template: {template}")
    for child in sorted(template.iterdir()):
        logger.info(f"Copying workspace template: {child}")
        if child.name.startswith("."):
            continue
        dest = workspace / child.name
        logger.info(f"Copying workspace template: {child} to {dest}")
        if child.is_dir():
            shutil.copytree(str(child), str(dest), dirs_exist_ok=True)
        else:
            shutil.copy2(str(child), str(dest))

    skills_dir = Path(agent_config.skills_dir)
    if agent_config.builtin_skills is not None and skills_dir.is_dir():
        logger.info(f"Keeping builtin skills: {agent_config.builtin_skills}")
        keep = frozenset(agent_config.builtin_skills)
        for child in list(skills_dir.iterdir()):
            if child.is_dir() and child.name not in keep:
                logger.info(f"Removing skill: {child} (not in builtin_skills)")
                shutil.rmtree(child)
            else:
                logger.info(f"Keeping skill: {child} (in builtin_skills)")
