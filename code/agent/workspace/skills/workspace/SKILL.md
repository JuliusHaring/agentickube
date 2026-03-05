---
name: workspace
description: Read, write, and list files in the agent workspace directory. Use for any file operation requested by the user.
---

# Workspace

You have tools for reading, writing, and listing files in your workspace. All paths are relative to the workspace root. Path traversal outside the workspace is rejected.

Use `list_dir` to explore, `read_file` to inspect, and `write_file` to create or update files.
