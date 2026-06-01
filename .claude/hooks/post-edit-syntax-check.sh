#!/bin/bash
# Runs after every Edit or Write. If the file is a .py file, checks syntax immediately.
# A non-zero exit tells Claude there was a problem so it can fix it before moving on.

file_path=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
")

if [[ "$file_path" == *.py ]]; then
    output=$(python3 -m py_compile "$file_path" 2>&1)
    if [[ $? -ne 0 ]]; then
        echo "Syntax error in $file_path:"
        echo "$output"
        exit 1
    fi
fi
