---
name: workspace
description: Read, write, and list files in the agent workspace directory. Use for any file operation requested by the user.
---

# Workspace

Read, write, and list files in the agent workspace. All paths are relative to the workspace root. Path traversal outside the workspace is rejected. Scripts use the WORKSPACE_DIR environment variable (default: /workspace).

## Scripts

### read_file.py

Read the contents of a file in the workspace.

**Usage:** `python read_file.py <relative_path>`

### write_file.py

Write content to a file in the workspace. Creates parent directories if needed.

**Usage:** `python write_file.py <relative_path> [content]`

If content is not provided as a second argument, reads from stdin.

### list_dir.py

List all entries in a directory recursively.

**Usage:** `python list_dir.py [relative_path]`

Defaults to the workspace root if no path given. Directories end with `/`.
