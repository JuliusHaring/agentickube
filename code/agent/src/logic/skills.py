"""Load SKILL.md files and code/ tool functions from skill directories."""

import importlib.util
import inspect
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from shared.logging import get_logger
from config import agent_config

logger = get_logger(__name__)


def _read_skill(path: Path) -> str | None:
    """Read a SKILL.md file and return its content, or None on error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning("Failed to read skill %s: %s", path, e)
        return None


def _discover_skills(directory: str) -> dict[str, Path]:
    """Discover skills in a directory. Returns {name: path_to_SKILL.md}.

    Supports two layouts:
      directory/skill-name/SKILL.md  (subdirectory per skill)
      directory/skill-name.md        (flat file)
    """
    root = Path(directory)
    logger.info(f"Discovering skills in {root}")
    if not root.is_dir():
        return {}

    skills: dict[str, Path] = {}
    for child in sorted(root.iterdir()):
        if child.is_dir():
            skill_md = child / "SKILL.md"
            if skill_md.is_file():
                skills[child.name] = skill_md
        elif child.is_file() and child.suffix == ".md":
            skills[child.stem] = child
    return skills


def _discover_skill_dirs(directory: str) -> dict[str, Path]:
    """Discover skill directories (not flat .md files) that have a code/ subfolder."""
    root = Path(directory)
    if not root.is_dir():
        return {}
    dirs: dict[str, Path] = {}
    for child in sorted(root.iterdir()):
        if (
            child.is_dir()
            and (child / "SKILL.md").is_file()
            and (child / "code").is_dir()
        ):
            dirs[child.name] = child
    return dirs


def _import_module_from_path(name: str, path: Path):
    """Dynamically import a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _collect_tools_from_skill(skill_name: str, skill_dir: Path) -> list[Callable]:
    """Import all .py files in skill_dir/code/ and collect public functions."""
    code_dir = skill_dir / "code"
    tools: list[Callable] = []
    for py_file in sorted(code_dir.glob("*.py")):
        module_name = f"skill_tools.{skill_name}.{py_file.stem}"
        try:
            module = _import_module_from_path(module_name, py_file)
        except Exception as e:
            logger.warning("Failed to import skill code %s: %s", py_file, e)
            continue
        for func_name, func in inspect.getmembers(module, inspect.isfunction):
            if func_name.startswith("_"):
                continue
            if func.__module__ != module_name:
                continue
            logger.info("Registered tool %s from skill %s", func_name, skill_name)
            tools.append(func)
    return tools


def _load_tools_from(
    directory: str, label: str, filter_names: list[str] | None = None
) -> list[Callable]:
    """Discover skill dirs with code/ in a directory and load their tools."""
    found = _discover_skill_dirs(directory)
    if filter_names is not None:
        found = {k: v for k, v in found.items() if k in filter_names}
    tools: list[Callable] = []
    for name, skill_dir in found.items():
        skill_tools = _collect_tools_from_skill(name, skill_dir)
        if skill_tools:
            logger.info(
                "Loaded %d tool(s) from %s skill: %s", len(skill_tools), label, name
            )
            tools.extend(skill_tools)
    return tools


def _load_from(
    directory: str, label: str, filter_names: list[str] | None = None
) -> list[str]:
    """Discover and load skills from a directory, optionally filtering by name."""
    found = _discover_skills(directory)
    if filter_names is not None:
        found = {k: v for k, v in found.items() if k in filter_names}
    contents: list[str] = []
    for name, path in found.items():
        text = _read_skill(path)
        if text:
            logger.info("Loaded %s skill: %s", label, name)
            contents.append(text)
    return contents


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
    if not template.is_dir():
        logger.debug("No workspace template at %s, skipping sync", template_dir)
        return

    workspace.mkdir(parents=True, exist_ok=True)
    logger.info("Syncing workspace from %s into %s", template_dir, workspace_dir)

    for child in sorted(template.iterdir()):
        if child.name.startswith("."):
            continue
        dest = workspace / child.name
        if child.is_dir():
            shutil.copytree(str(child), str(dest), dirs_exist_ok=True)
        else:
            shutil.copy2(str(child), str(dest))

    # If builtin_skills is set (including []), keep only those skills; remove all others.
    skills_dir = workspace / "skills"
    if agent_config.builtin_skills is not None and skills_dir.is_dir():
        keep = frozenset(agent_config.builtin_skills)
        for child in list(skills_dir.iterdir()):
            if child.is_dir() and child.name not in keep:
                shutil.rmtree(child)
                logger.info("Removed skill '%s' (not in builtin_skills)", child.name)


def load_skills() -> list[str]:
    """Load all skills from {workspace}/skills/.

    Built-ins and operator-provided skills are seeded there at startup.
    Agent-created skills are written there at runtime and picked up immediately.
    """
    contents = _load_from(agent_config.skills_dir, "workspace")
    logger.info("Loaded %d skills total", len(contents))
    return contents


def load_skill_tools() -> list[Callable]:
    """Load Python tool functions from {workspace}/skills/."""
    tools = _load_tools_from(agent_config.skills_dir, "workspace")
    logger.info("Loaded %d skill tools total", len(tools))
    return tools
