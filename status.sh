#!/bin/bash
cd "$(dirname "$0")"

PID_FILE=".bot.pid"
LOG_FILE="bot.log"

echo "=========================================="
echo "Claude Webex Bridge - Status"
echo "=========================================="
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "Status: ❌ Not running"
    exit 0
fi

PID=$(cat "$PID_FILE")

# Check if process is actually running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Status: ❌ Not running (stale PID file)"
    rm "$PID_FILE"
    exit 0
fi

echo "Status: ✅ Running"
echo "PID: $PID"
echo ""

# Show process info
echo "Process info:"
ps -p "$PID" -o pid,ppid,etime,rss,command | tail -n +2

# Show last log lines if log file exists
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo "Last 5 log entries:"
    echo "----------------------------------------"
    tail -5 "$LOG_FILE"
fi

echo ""
echo "Commands:"
echo "  ./logs.sh - View full logs"
echo "  ./stop.sh - Stop the bot"
