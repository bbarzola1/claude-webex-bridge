#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "Claude Webex Bridge - Setup"
echo "=========================================="
echo ""

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

# Create virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate venv and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip3 install -q --upgrade pip
pip3 install -q -r requirements.txt
echo "✓ Dependencies installed"

# Setup .env file
if [ -f ".env" ]; then
    echo "✓ .env file already exists"
    read -p "Overwrite existing .env? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping .env setup"
    else
        rm .env
    fi
fi

if [ ! -f ".env" ]; then
    echo ""
    echo "Setting up .env configuration..."
    echo ""

    # Prompt for bot token
    echo "Enter your Webex Bot Access Token:"
    echo "(Get it from: https://developer.webex.com/my-apps)"
    read -r BOT_TOKEN

    # Prompt for email
    echo ""
    echo "Enter your Webex email address:"
    echo "(Only this email will be able to use the bot)"
    read -r USER_EMAIL

    # Write .env file
    cat > .env <<EOF
WEBEX_BOT_TOKEN=$BOT_TOKEN
WEBEX_USER_EMAIL=$USER_EMAIL
EOF

    echo "✓ .env file created"
fi

# Make scripts executable
chmod +x start.sh stop.sh status.sh logs.sh 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Webex and message your bot to create a 1:1 room"
echo "2. Run: ./start.sh"
echo "3. Send commands to your bot in Webex"
echo ""
echo "Available scripts:"
echo "  ./start.sh  - Start the bot"
echo "  ./stop.sh   - Stop the bot"
echo "  ./status.sh - Check bot status"
echo "  ./logs.sh   - View bot logs"
echo ""
