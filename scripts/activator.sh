#!/usr/bin/env bash
# Activates self-improving hook flows for user prompts and pending summaries.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
EVENT="${1:-UserPromptSubmit}"

case "$EVENT" in
  UserPromptSubmit)
    PROMPT="${2:-}"
    python -m app.self_improving.hooks UserPromptSubmit --project-root "$PROJECT_ROOT" --prompt "$PROMPT"
    ;;
  ListPending)
    python -m app.self_improving.hooks ListPending --project-root "$PROJECT_ROOT"
    ;;
  PromoteLearning)
    LEARNING_ID="${2:-}"
    RATIONALE="${3:-}"
    python -m app.self_improving.hooks PromoteLearning --project-root "$PROJECT_ROOT" --learning-id "$LEARNING_ID" --rationale "$RATIONALE"
    ;;
  *)
    echo "Unsupported event: $EVENT" >&2
    exit 1
    ;;
esac
