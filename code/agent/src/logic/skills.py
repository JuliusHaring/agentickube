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


def seed_workspace_skills(
    builtin_dir: str = agent_config.skills_builtin_dir,
    bootstrap_dir: str | None = None,
    workspace_dir: str = agent_config.workspace_dir,
) -> None:
    """Seed all skills into {workspace}/skills/ on startup.

    Sources (both overwrite existing files so the image/CR stays authoritative):
      1. Built-in skills from the image, filtered by SKILLS_BUILTINS env var.
      2. Operator-provided bootstrap skills (flat *.md → <stem>/SKILL.md; dirs copied as-is).

    After seeding, {workspace}/skills/ is the single source of truth.
    Agent-created skills are written there directly at runtime.
    """
    skills_dir = Path(workspace_dir) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Compute builtin filter from config (SKILLS_BUILTINS env var).
    builtin_filter: list[str] | None = None
    if agent_config.skills_builtins is not None:
        raw = agent_config.skills_builtins.strip()
        builtin_filter = [s.strip() for s in raw.split(",") if s.strip()] if raw else []

    # 1. Seed built-in skills from the image directory.
    builtin_root = Path(builtin_dir)
    if builtin_root.is_dir():
        for child in sorted(builtin_root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").is_file():
                if builtin_filter is not None and child.name not in builtin_filter:
                    logger.debug(
                        "Skipping built-in skill '%s' (filtered out)", child.name
                    )
                    continue
                dest = skills_dir / child.name
                shutil.copytree(str(child), str(dest), dirs_exist_ok=True)
                logger.info("Seeded built-in skill '%s' into workspace", child.name)

    # 2. Seed operator-provided bootstrap skills (ConfigMap-sourced).
    if bootstrap_dir is None:
        bootstrap_dir = agent_config.skills_bootstrap_dir
    if not bootstrap_dir:
        return
    bootstrap = Path(bootstrap_dir)
    if not bootstrap.is_dir():
        logger.warning("Skills bootstrap dir not found: %s", bootstrap_dir)
        return

    for entry in sorted(bootstrap.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            dest = skills_dir / entry.stem / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(entry.read_text(encoding="utf-8"))
            logger.info("Seeded skill '%s' from bootstrap", entry.stem)
        elif entry.is_dir():
            dest_dir = skills_dir / entry.name
            shutil.copytree(str(entry), str(dest_dir), dirs_exist_ok=True)
            logger.info("Seeded skill directory '%s' from bootstrap", entry.name)


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
