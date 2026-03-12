---
name: create-skill
description: Creates new agent skills in the workspace. Enforces correct location, name, and description; no subprocess; external data via httpx or requests only; proper errors. Use when the user wants to create or scaffold a new skill.
---

# Create Skill

Use this skill to create new agent skills under a given skills root. The implementation uses **bare Python only** (standard library); no external packages may be installed. If creation cannot be completed, the code **must raise an error** — it must not silently fail or return a generic success.

## Location and layout

- Skills live under a single **skills root** directory (e.g. `code/agent/workspace/skills`).
- Each skill is a **directory** with a `SKILL.md` file at the top level.
- **Skill code lives under `<skill-name>/code/...`** — e.g. `create-skill/code/create_skill.py`, `my-tool/code/helper.py`. When creating a skill, the scaffold includes an empty `code/` subdirectory.

The code enforces that the skill is created **in the right place**: the skill directory must be a direct child of the given skills root, and the path must not escape the skills root.

## Name and description rules

- **Name**: lowercase letters, numbers, and hyphens only; max 64 characters. Used as the directory name and in SKILL.md frontmatter.
- **Description**: non-empty, max 1024 characters. Used in SKILL.md frontmatter so the agent can discover when to apply the skill.

If the name or description is invalid, the code **must raise** a clear error (e.g. `ValueError` with an explanatory message).

## Generic skills

Created skills should be **generic**, not tied to a single use case (e.g. a skill that works for any input, not one hard-coded example). The SKILL.md and code should describe and implement the general capability so the agent can use it in multiple cases.

**Do not create a skill named fetch-stocks.** If the user asks for stock or quote data, use existing tools (e.g. fetch_stock if available) or respond that the capability is not available; do not create a new skill for fetching stocks. Never use yfinance; use requests or httpx only for HTTP.

## External data and subprocess

- **Subprocess**: **Subprocess must not be used.** No `subprocess`, `os.system`, or equivalent. File and directory creation must be done with standard library file I/O only (e.g. `pathlib`, `open`).
- **Imports**: Do not import any library that is not python native. Allowed are httpx and requests.

## Errors

- **Proper errors**: The skill code must raise explicit exceptions for invalid or impossible operations. Do not return error strings or sentinel values when something is wrong — raise (e.g. `ValueError`, `FileExistsError`, `OSError`) with a clear message.
- **No external modules**: The create-skill implementation itself uses only the Python standard library. If a required operation cannot be done without installing a package, the code must **raise an error** explaining what is missing rather than attempting to install or use an uninstalled module.
- **Cannot create**: If the skill cannot be created (e.g. name already exists, invalid name, permission error, path escapes root), the code must **raise an error** and must not create partial or incorrect files.

## Config

The code may use `from config import agent_config`, which provides `workspace_dir` and `skills_dir` (workspace + `"skills"`). If no skills root is passed, both helpers default to `agent_config.skills_dir`.

## Usage

- **check_skill_exists(skill_name, skills_root=None)**  
  Returns whether a skill directory already exists and contains a `SKILL.md` file. Uses `agent_config.skills_dir` when `skills_root` is omitted. Validates that `skill_name` is a valid name (same rules as above); raises if not.

- **create_skill(skill_name, description, body_md="", skills_root=None)**  
  **Requires both skill_name and description** (pass both every time). Do not create a skill named fetch-stocks. Creates the skill directory, an empty `code/` subdirectory, and a minimal `SKILL.md`. This is a **scaffold only** — the agent must then add the implementation under `code/` using **requests or httpx only** for any HTTP/API (no yfinance). Use workspace/file tools to write the code. Uses `agent_config.skills_dir` when `skills_root` is omitted. Raises if the skill already exists, if inputs are invalid, or if creation fails. Does not use subprocess; uses only stdlib file I/O.
