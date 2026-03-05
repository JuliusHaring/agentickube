"""
Pydantic-ai tools for reading/writing files in the agent workspace (WORKSPACE_DIR).
Paths are relative to the workspace root; path traversal outside the workspace is rejected.
"""

from pathlib import Path

from config import llm_config


def _resolve_path(relative_path: str) -> Path:
    """Resolve path relative to workspace; raise ValueError if it escapes the workspace."""
    raw = (relative_path or "").strip()
    if not llm_config.workspace_dir:
        raise ValueError("Workspace directory is not set")
    workspace_root = Path(llm_config.workspace_dir).resolve()
    if not raw or raw == "." or raw == "/" or raw.rstrip("/") == str(workspace_root):
        return workspace_root
    path = (workspace_root / raw).resolve()
    try:
        path.resolve().relative_to(workspace_root)
    except ValueError:
        raise ValueError(f"Path must stay inside workspace ({workspace_root})")
    return path


def read_file(path: str) -> str:
    """Read the contents of a file in the workspace.

    Args:
        path: Path relative to the workspace root (e.g. 'notes.txt' or 'subdir/file.txt').
    """
    try:
        p = _resolve_path(path)
    except ValueError as e:
        return f"Error: {e}"
    if not p.is_file():
        return f"Error: not a file or does not exist: {path}"
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file in the workspace. Creates parent directories if needed.

    Args:
        path: Path relative to the workspace root.
        content: Text to write.
    """
    try:
        p = _resolve_path(path)
    except ValueError as e:
        return f"Error: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {path}"
    except OSError as e:
        return f"Error writing {path}: {e}"


def _list_dir_recursive(dir_path: Path, base: Path) -> list[str]:
    """Yield relative path strings (directories with /) under dir_path, sorted."""
    lines = []
    try:
        entries = sorted(
            dir_path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())
        )
    except OSError:
        return lines
    for e in entries:
        rel = e.relative_to(base)
        lines.append(f"{rel}/" if e.is_dir() else str(rel))
        if e.is_dir():
            lines.extend(_list_dir_recursive(e, base))
    return lines


def list_dir(path: str = ".") -> str:
    """List all entries in a directory recursively (subdirectories and their contents).

    Args:
        path: Directory path relative to the workspace root; use '.' for the workspace root.

    Returns:
        Newline-separated list of paths relative to the given directory; directories end with '/'.
    """
    try:
        p = _resolve_path(path)
    except ValueError as e:
        return f"Error: {e}"
    if not p.exists():
        return f"Error: path does not exist: {path}"
    if not p.is_dir():
        return f"Error: not a directory: {path}"
    try:
        lines = _list_dir_recursive(p, p)
        return "\n".join(lines) if lines else "(empty)"
    except OSError as e:
        return f"Error listing {path}: {e}"


def workspace_toolset() -> list:
    """Return the list of workspace tool functions for pydantic-ai Agent(tools=...)."""
    if not llm_config.workspace_dir:
        raise ValueError("Workspace directory is not set")
    return [read_file, write_file, list_dir]
