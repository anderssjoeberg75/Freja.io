#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"

# Detect unresolved git conflict markers at line start.
if rg -n "^(<<<<<<<|>>>>>>>)" "$ROOT_DIR" \
  --glob '!.git/**' \
  --glob '!**/__pycache__/**' \
  --glob '!**/*.pyc'; then
  echo "Found unresolved merge conflict markers."
  exit 1
fi

echo "No unresolved merge conflict markers found."
