#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "Claude Webex Bridge - Setup"
echo "=========================================="
echo ""

# ---------- Prerequisites ----------

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_OK=$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 9) else 0)')
echo "✓ Found Python $PYTHON_VERSION"

if [ "$PYTHON_OK" != "1" ]; then
    echo "❌ Error: Python 3.9 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "⚠️  Warning: 'claude' CLI not found on PATH."
    echo "   The bot requires Claude Code to be installed."
    echo "   Visit: https://docs.anthropic.com/en/docs/claude-code"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ---------- Virtual environment & dependencies ----------

if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo "Installing dependencies..."
source venv/bin/activate
pip3 install -q --upgrade pip
pip3 install -q -r requirements.txt
echo "✓ Dependencies installed"

# ---------- .env configuration ----------

if [ -f ".env" ]; then
    echo "✓ .env file already exists"
    read -p "Overwrite existing .env? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping .env setup"
        SKIP_ENV=1
    else
        rm .env
    fi
fi

if [ -z "$SKIP_ENV" ] && [ ! -f ".env" ]; then
    echo ""
    echo "=========================================="
    echo "Step 1: Create your Webex bot"
    echo "=========================================="
    echo ""
    echo "Opening the Webex developer portal in your browser..."
    echo "Create a new bot there, then copy the Bot Access Token."
    echo ""

    # Open browser to bot creation page (works on macOS, Linux, WSL)
    URL="https://developer.webex.com/my-apps/new/bot"
    if command -v open &> /dev/null; then
        open "$URL"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$URL"
    elif command -v wslview &> /dev/null; then
        wslview "$URL"
    else
        echo "Could not open browser automatically."
        echo "Please visit: $URL"
    fi

    echo "Fill in the bot details on the page, then copy the token."
    echo ""
    read -p "Paste your Bot Access Token here: " -r BOT_TOKEN
    echo ""

    # Validate the token
    echo "Validating token..."
    VALIDATE_RESULT=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $BOT_TOKEN" \
        "https://webexapis.com/v1/people/me" 2>/dev/null)

    HTTP_CODE=$(echo "$VALIDATE_RESULT" | tail -1)
    BODY=$(echo "$VALIDATE_RESULT" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        BOT_NAME=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('displayName','(unknown)'))" 2>/dev/null || echo "(unknown)")
        echo "✓ Token valid — bot name: $BOT_NAME"
    else
        echo "❌ Token validation failed (HTTP $HTTP_CODE)."
        echo "   Make sure you copied the full token."
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "Step 2: Your Webex email"
    echo "=========================================="
    echo ""
    echo "Only this email will be able to use the bot."
    read -p "Enter your Webex email: " -r USER_EMAIL
    echo ""

    # Write .env file
    cat > .env <<EOF
WEBEX_BOT_TOKEN=$BOT_TOKEN
WEBEX_USER_EMAIL=$USER_EMAIL
EOF

    echo "✓ .env file created"
fi

# ---------- Finish ----------

# Make scripts executable
chmod +x start.sh stop.sh status.sh logs.sh 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Run: ./start.sh"
echo "The bot will message you in Webex automatically."
echo ""
echo "Available scripts:"
echo "  ./start.sh  - Start the bot"
echo "  ./stop.sh   - Stop the bot"
echo "  ./status.sh - Check bot status"
echo "  ./logs.sh   - View bot logs"
echo ""
