#!/usr/bin/env bash
# PreToolUse (Bash) for read-only subagents: refuse commands that write files or change the warehouse.
# Tested in tests/test_hooks.py. Comparisons like `price > 5` inside a query are allowed;
# redirects into files, file-moving commands and write SQL are not.
CMD=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')

blocked() { echo "Blocked: this agent is read-only ($1). Report the finding instead of changing anything." >&2; exit 2; }

echo "$CMD" | grep -Eq '(^|[;&|[:space:]])(rm|mv|cp|tee|truncate|chmod|touch)[[:space:]]' && blocked "file command"
echo "$CMD" | grep -Eq 'sed[[:space:]]+-i' && blocked "in-place edit"
echo "$CMD" | grep -Eq '>{1,2}[[:space:]]*[[:alnum:]_./~-]+\.(csv|txt|json|md|sql|py|yaml|yml|duckdb|parquet|DAT)\b' && blocked "redirect into a file"
echo "$CMD" | grep -Eiq '\b(insert[[:space:]]+into|update[[:space:]]+[[:alnum:]_]+[[:space:]]+set|delete[[:space:]]+from|drop[[:space:]]+(table|view|schema)|create[[:space:]]+(or[[:space:]]+replace[[:space:]]+)?(table|view)|alter[[:space:]]+table|copy[[:space:]]+[[:alnum:]_(]+.*[[:space:]]to[[:space:]])' && blocked "write SQL"
echo "$CMD" | grep -Eq 'read_only[[:space:]]*=[[:space:]]*False' && blocked "read-write connection"
exit 0
