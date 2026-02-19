#!/bin/bash

echo "Restarting Claude Webex Bridge..."
echo ""

# Stop the bot
./stop.sh

# Wait a moment
sleep 1

# Start the bot
./start.sh
