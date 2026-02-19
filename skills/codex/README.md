# Codex Skill

## What this skill does

The Codex skill allows Freja to operate as an engineering assistant that can run code, execute shell commands in a sandbox, perform Git actions, and audit the codebase.

## Main capabilities

- Execute Python and shell commands in Docker sandbox
- Perform repository operations (clone, checkout, status, log, commit, push)
- Trigger internal code audit reports

## Registered Freja tools

- `execute_codex_code`
- `tool_code_executor` (alias)
- `run_code` (alias)
- `codex_git_ops`
- `codex_audit_codebase`
- `tool_analyze_code` (alias)

## How to use it via Freja

### Natural language examples

- `Run this Python snippet and show output.`
- `Check git status in the current repository.`
- `Create a commit with message: update docs.`
- `Run a self-audit of the codebase.`

### Direct tool call examples

```json
{
  "tool": "execute_codex_code",
  "args": {
    "language": "shell",
    "code": "pytest -q"
  }
}
```

```json
{
  "tool": "codex_git_ops",
  "args": {
    "action": "status"
  }
}
```

## Requirements

- Docker must be installed and available for sandbox execution.
- Git must be available for repository operations.
