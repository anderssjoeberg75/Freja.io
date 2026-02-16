---
name: Freja Codex
description: Advanced coding agent capable of executing code, running tests, and managing version control.
---

# Freja Codex

This skill empowers Freja to act as an autonomous software engineer. It provides tools to safely execute code in a Docker sandbox, run test suites, manage Git repositories, and perform self-analysis.

## Capabilities

- **Safe Execution**: Run Python scripts and shell commands in an isolated Docker container.
- **Test Automation**: Execute unit tests (pytest) and analyze results.
- **Version Control**: Clone, branch, commit, and push code to GitHub.
- **Self-Evolution**: Analyze Freja's own source code to identify bugs and improvements.

## Tools

### 1. `execute_code`
Runs Python code or Shell commands in the sandbox.
- **Use for**: "Run this script", "Test this function", "List files".

### 2. `git_ops`
Performs Git operations.
- **Use for**: "Commit changes", "Create a new branch", "Push to GitHub".

### 3. `audit_code`
Triggers a comprehensive code analysis of the project.
- **Use for**: "Analyze the codebase", "Find bugs in app/core".
