#!/usr/bin/env python3
"""Read a file from the workspace directory.

Usage: python read_file.py <relative_path>

WORKSPACE_DIR env var sets the workspace root (default: /workspace).
"""

import os
import sys
from pathlib import Path


def _resolve(relative_path: str) -> Path:
    workspace_root = Path(os.environ.get("WORKSPACE_DIR", "/workspace")).resolve()
    raw = (relative_path or "").strip()
    if not raw or raw in (".", "/"):
        raise ValueError("Must provide a file path, not directory root")
    path = (workspace_root / raw).resolve()
    if not path.is_relative_to(workspace_root):
        raise ValueError(f"Path must stay inside workspace ({workspace_root})")
    return path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: read_file.py <relative_path>", file=sys.stderr)
        sys.exit(1)

    try:
        p = _resolve(sys.argv[1])
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not p.is_file():
        print(f"Error: not a file or does not exist: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    try:
        print(p.read_text(encoding="utf-8", errors="replace"))
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
