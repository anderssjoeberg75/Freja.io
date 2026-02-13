#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/anderssjoeberg75/Freja.io.git"
TARGET_BRANCH="main"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

if ! command -v git >/dev/null 2>&1; then
  echo "git is not installed"
  exit 1
fi

if [ ! -d .git ]; then
  echo "This directory is not a git repository: $REPO_ROOT"
  exit 1
fi

CURRENT_REMOTE="$(git remote get-url origin 2>/dev/null || true)"
if [ -z "$CURRENT_REMOTE" ]; then
  git remote add origin "$REPO_URL"
elif [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
  git remote set-url origin "$REPO_URL"
fi

git fetch origin "$TARGET_BRANCH"
git reset --hard "origin/$TARGET_BRANCH"
git clean -fd

if [ ! -x "$REPO_ROOT/start.sh" ]; then
  chmod +x "$REPO_ROOT/start.sh"
fi

nohup "$REPO_ROOT/start.sh" > "$REPO_ROOT/.self_update_start.log" 2>&1 &

echo "Update completed and start.sh launched."
