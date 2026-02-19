#!/bin/bash

PID_FILE=".bot.pid"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "❌ Bot is not running (no PID file found)"
    exit 1
fi

PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ Bot is not running (stale PID file)"
    rm "$PID_FILE"
    exit 1
fi

echo "Stopping bot (PID: $PID)..."

# Try graceful shutdown first (SIGTERM)
kill "$PID" 2>/dev/null

# Wait up to 5 seconds for graceful shutdown
for i in {1..5}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Bot stopped successfully"
        rm "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
echo "⚠️  Bot didn't stop gracefully, forcing shutdown..."
kill -9 "$PID" 2>/dev/null
sleep 1

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Bot stopped (forced)"
    rm "$PID_FILE"
    exit 0
else
    echo "❌ Failed to stop bot"
    exit 1
fi
