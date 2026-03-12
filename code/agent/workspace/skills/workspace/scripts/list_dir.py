#!/usr/bin/env python3
"""List files and directories in the workspace recursively.

Usage: python list_dir.py [relative_path]

Defaults to workspace root if no path given.
WORKSPACE_DIR env var sets the workspace root (default: /workspace).
"""

import os
import sys
from pathlib import Path


def _resolve(relative_path: str) -> Path:
    workspace_root = Path(os.environ.get("WORKSPACE_DIR", "/workspace")).resolve()
    raw = (relative_path or "").strip()
    if not raw or raw in (".", "/"):
        return workspace_root
    path = (workspace_root / raw).resolve()
    if not path.is_relative_to(workspace_root):
        raise ValueError(f"Path must stay inside workspace ({workspace_root})")
    return path


def _list_recursive(dir_path: Path, base: Path) -> list[str]:
    lines: list[str] = []
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
            lines.extend(_list_recursive(e, base))
    return lines


def main() -> None:
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "."

    try:
        p = _resolve(path_arg)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not p.exists():
        print(f"Error: path does not exist: {path_arg}", file=sys.stderr)
        sys.exit(1)
    if not p.is_dir():
        print(f"Error: not a directory: {path_arg}", file=sys.stderr)
        sys.exit(1)

    lines = _list_recursive(p, p)
    print("\n".join(lines) if lines else "(empty)")


if __name__ == "__main__":
    main()
