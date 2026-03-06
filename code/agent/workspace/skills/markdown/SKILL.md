---
name: markdown
description: Parse and convert markdown to HTML. Use when the user has markdown text and wants it rendered, converted to HTML, or normalized.
---

# Markdown

Use the tools in this skill to parse and convert markdown text (e.g. to HTML).

## When to use

- User has markdown text and wants it parsed (e.g. converted to HTML or normalized).
- User wants to render or structure markdown for display or further processing.

## Tools

- **parse_markdown**: Converts markdown text to HTML. Use when you need to render or structure markdown (e.g. for display or further processing).

## Notes

- Input can be raw markdown from files, APIs, or other sources. Empty input returns empty string.
- Uses the "extra" extension for tables, fenced code blocks, and similar syntax.
