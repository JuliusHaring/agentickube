---
name: markdown
description: Parse and convert markdown to HTML. Use when the user has markdown text and wants it rendered, converted to HTML, or normalized.
---

# Markdown

Parse and convert markdown text to HTML.

## When to use

- User has markdown text and wants it parsed (e.g. converted to HTML or normalized).
- User wants to render or structure markdown for display or further processing.

## Scripts

### parse_markdown.py

Converts markdown text to HTML. Uses the "extra" extension for tables, fenced code blocks, and similar syntax.

**Usage:**
- From stdin: `echo "# Hello" | python parse_markdown.py`
- From file: `python parse_markdown.py path/to/file.md`

Output is HTML printed to stdout. Empty input produces no output.
