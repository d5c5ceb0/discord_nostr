#!/bin/bash

project_path=$(pwd)
venv_path="$project_path/.venv"

# Create logs directory if it doesn't exist
if [ ! -d "$project_path/discord_nostr/logs" ]; then
    mkdir -p "$project_path/discord_nostr/logs"
fi

# Kill all Python processes containing 'main'
ps aux | grep python | grep main | grep -v grep | awk '{print $2}' | xargs -r kill -9

# Wait a moment to ensure processes are killed
sleep 1

# Start the new Python process using virtualenv python
nohup "$venv_path/bin/python" "$project_path/discord_nostr/main.py" >"$project_path/discord_nostr/logs/main.log" 2>&1 &

sleep 2

# Print confirmation
echo "Previous processes killed and new process started in $project_path using virtualenv Python"