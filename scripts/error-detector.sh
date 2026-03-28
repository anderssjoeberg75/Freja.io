#!/usr/bin/env bash
# Detects failed tool runs and logs ERROR entries through the PostToolUse hook.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TOOL_NAME="${1:-unknown_tool}"
TOOL_ARGS_JSON="${2:-{}}"
RESULT_JSON="${3:-{\"ok\":false,\"text\":\"unknown failure\"}}"

python -m app.self_improving.hooks PostToolUse \
  --project-root "$PROJECT_ROOT" \
  --tool-name "$TOOL_NAME" \
  --tool-args "$TOOL_ARGS_JSON" \
  --result "$RESULT_JSON"
