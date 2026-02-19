#!/bin/bash
cd "$(dirname "$0")"

PID_FILE=".bot.pid"
LOG_FILE="bot.log"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "❌ Bot is already running (PID: $PID)"
        echo "   Use ./stop.sh to stop it first"
        exit 1
    else
        # Stale PID file, remove it
        rm "$PID_FILE"
    fi
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Run ./setup.sh first"
    exit 1
fi

echo "Starting Claude Webex Bridge..."

# Activate venv and start bot in background
source venv/bin/activate
nohup python3 bot.py >> "$LOG_FILE" 2>&1 &
BOT_PID=$!

# Save PID
echo $BOT_PID > "$PID_FILE"

# Wait a moment to check if it started successfully
sleep 2

if ps -p "$BOT_PID" > /dev/null 2>&1; then
    echo "✅ Bot started successfully (PID: $BOT_PID)"
    echo ""
    echo "Commands:"
    echo "  ./status.sh - Check bot status"
    echo "  ./logs.sh   - View logs"
    echo "  ./stop.sh   - Stop the bot"
else
    echo "❌ Bot failed to start. Check logs with: ./logs.sh"
    rm "$PID_FILE"
    exit 1
fi
