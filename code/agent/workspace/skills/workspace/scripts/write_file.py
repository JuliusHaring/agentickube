#!/usr/bin/env python3
"""Write content to a file in the workspace directory.

Usage: python write_file.py <relative_path> [content]

If content is not provided as a second argument, reads from stdin.
WORKSPACE_DIR env var sets the workspace root (default: /workspace).
"""

import os
import sys
from pathlib import Path


def _resolve(relative_path: str) -> Path:
    workspace_root = Path(os.environ.get("WORKSPACE_DIR", "/workspace")).resolve()
    raw = (relative_path or "").strip()
    if not raw or raw in (".", "/"):
        raise ValueError("Must provide a file path")
    path = (workspace_root / raw).resolve()
    if not path.is_relative_to(workspace_root):
        raise ValueError(f"Path must stay inside workspace ({workspace_root})")
    return path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: write_file.py <relative_path> [content]", file=sys.stderr)
        sys.exit(1)

    try:
        p = _resolve(sys.argv[1])
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 2:
        content = sys.argv[2]
    else:
        content = sys.stdin.read()

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print(f"Wrote {sys.argv[1]}")
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
