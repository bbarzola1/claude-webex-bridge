#!/bin/bash
cd "$(dirname "$0")"

echo "Restarting Claude Webex Bridge..."
echo ""

# Stop the bot (exit code ignored — bot may not be running, that's OK)
./stop.sh || true

# Wait a moment
sleep 1

# Start the bot
./start.sh
