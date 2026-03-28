#!/usr/bin/env bash
# Extracts high-value learning summaries that can be converted into durable skills.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LEARNINGS_FILE="$PROJECT_ROOT/.learnings/LEARNINGS.md"

if [[ ! -f "$LEARNINGS_FILE" ]]; then
  echo "No learnings file found at $LEARNINGS_FILE" >&2
  exit 1
fi

awk '
  /^## / {heading=$0}
  /^### Summary/ {getline; summary=$0; if (summary != "") {print heading "\n- SkillCandidate: " summary "\n"}}
' "$LEARNINGS_FILE"
