#!/bin/bash
# Runs before every Bash call. Blocks any rm command that targets a path
# outside the project directory without explicit approval.

PROJECT_DIR="/Users/jaykreusch/Documents/BB Lightweight Inventory"

cmd=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
")

# Only inspect commands that contain rm
if ! echo "$cmd" | grep -qE '\brm\b'; then
    exit 0
fi

# If rm is present, check whether all targeted paths are inside the project.
# Look for absolute paths (/...) or home-relative paths (~...) in the command.
# If any exist that don't start with the project dir, block and explain.
outside=$(echo "$cmd" | grep -oE '(/[^ ]+|~[^ ]*)' | grep -v "^${PROJECT_DIR}")

if [[ -n "$outside" ]]; then
    echo "BLOCKED: rm command targets a path outside the project directory."
    echo ""
    echo "Command : $cmd"
    echo "Path(s) : $outside"
    echo ""
    echo "If this is intentional, run it manually in your terminal."
    exit 1
fi
