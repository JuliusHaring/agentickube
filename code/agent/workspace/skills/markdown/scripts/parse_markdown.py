#!/usr/bin/env python3
"""Parse markdown text to HTML. Reads from stdin or from a file path argument."""

import sys

import markdown


def main() -> None:
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"Error reading {path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        return

    print(markdown.markdown(text.strip(), extensions=["extra"]))


if __name__ == "__main__":
    main()
