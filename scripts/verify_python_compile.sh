#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q app main.py

echo "Python compilation check passed."
