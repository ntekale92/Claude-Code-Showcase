#!/usr/bin/env bash
# Stop hook: if code, SQL, checks or metric cards changed, Claude can't finish until `make check` passes.
# Guarded by stop_hook_active so it never loops forever.
INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())')
[ "$ACTIVE" = "true" ] && exit 0

cd "$CLAUDE_PROJECT_DIR" || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

CHANGED=$(git status --porcelain -- src models quality metrics evals tests 2>/dev/null)
[ -z "$CHANGED" ] && exit 0

if ! out=$(make check 2>&1); then
  echo "make check is failing. Fix it before finishing:" >&2
  echo "$out" | tail -n 25 >&2
  exit 2
fi
exit 0
