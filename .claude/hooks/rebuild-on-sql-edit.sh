#!/usr/bin/env bash
# PostToolUse on models/**/*.sql: rebuild the sample warehouse (under a second) so a broken model
# is caught on the edit that broke it, not three edits later. Exit 2 feeds the error back to Claude.
cd "$CLAUDE_PROJECT_DIR" || exit 0

if ! out=$(DATA_MODE=sample PYTHONPATH=src python3 -m oda.pipeline 2>&1); then
  echo "SQL model failed to build after this edit:" >&2
  echo "$out" | tail -n 15 >&2
  exit 2
fi
exit 0
