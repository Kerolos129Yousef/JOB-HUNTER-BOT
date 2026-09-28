#!/usr/bin/env bash
# Wrapper for cron: runs one polling cycle of the bot.
set -euo pipefail

# Directory of this script (so cron can call it from anywhere).
cd "$(dirname "$0")"

# Use the project virtualenv if it exists, otherwise system python3.
if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
else
    PY="python3"
fi

exec "$PY" main.py "$@" >> job-hunter.log 2>&1
