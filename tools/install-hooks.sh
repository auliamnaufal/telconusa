#!/usr/bin/env bash
# Point git at the versioned hooks in tools/hooks (run once per clone).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

git config core.hooksPath tools/hooks
chmod +x tools/hooks/*

echo "Git hooks installed: core.hooksPath=tools/hooks"
for hook in tools/hooks/*; do
  echo "  - $(basename "$hook")"
done
