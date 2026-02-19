#!/bin/bash
cd "$(dirname "$0")"

LOG_FILE="bot.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "   The bot may not have been started yet."
    exit 1
fi

# Check if -f flag is passed for follow mode
if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
    echo "Following logs (Ctrl+C to exit)..."
    echo "=========================================="
    tail -f "$LOG_FILE"
else
    echo "Showing recent logs (use -f to follow)..."
    echo "=========================================="
    tail -50 "$LOG_FILE"
    echo ""
    echo "Tip: Use './logs.sh -f' to follow logs in real-time"
fi
