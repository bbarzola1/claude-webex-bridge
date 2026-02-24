#!/usr/bin/env python3
"""
Claude Webex Bridge - One-click setup and run.

Usage:
    python3 run.py            Setup (if needed) and start the bot
    python3 run.py --setup    Force re-run setup
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_PYTHON = (3, 9)
VENV_DIR = "venv"
REQUIREMENTS_FILE = "requirements.txt"
ENV_FILE = ".env"
WEBEX_BOT_URL = "https://developer.webex.com/my-apps/new/bot"
WEBEX_ME_URL = "https://webexapis.com/v1/people/me"

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

# Enable ANSI escapes on Windows 10+
if sys.platform == "win32":
    try:
        os.system("")
    except Exception:
        BOLD = GREEN = YELLOW = RED = DIM = RESET = ""


def _ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def _warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")


def _err(msg):
    print(f"  {RED}✗{RESET} {msg}")


def _banner():
    print(
        f"\n{BOLD}"
        "==========================================\n"
        "  Claude Webex Bridge\n"
        "==========================================\n"
        f"{RESET}"
    )


def _heading(text):
    print(f"\n{BOLD}{text}{RESET}\n")


# ---------------------------------------------------------------------------
# Path helpers (cross-platform venv paths)
# ---------------------------------------------------------------------------

def _venv_python():
    if sys.platform == "win32":
        return Path(VENV_DIR) / "Scripts" / "python.exe"
    return Path(VENV_DIR) / "bin" / "python3"


def _venv_pip():
    if sys.platform == "win32":
        return Path(VENV_DIR) / "Scripts" / "pip.exe"
    return Path(VENV_DIR) / "bin" / "pip3"


# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------

def _check_python():
    v = sys.version_info[:2]
    if v < MIN_PYTHON:
        _err(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required (found {v[0]}.{v[1]})")
        sys.exit(1)
    _ok(f"Python {v[0]}.{v[1]}")


def _check_claude_cli():
    if shutil.which("claude"):
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            version = result.stdout.strip() or "installed"
            _ok(f"Claude CLI ({version})")
        except Exception:
            _ok("Claude CLI found")
        return True

    _warn("Claude CLI not found on PATH")
    print()
    print("    The bot needs Claude Code to work.")
    print("    Install it with:")
    print()
    print(f"      {BOLD}npm install -g @anthropic-ai/claude-code{RESET}")
    print()
    print("    Then run 'claude' once to sign in.")
    print()
    resp = input("    Continue without it? (y/n): ").strip().lower()
    return resp in ("y", "yes")


# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

def _setup_venv():
    venv_python = _venv_python()

    if venv_python.exists():
        _ok("Virtual environment exists")
    else:
        print("  Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            check=True,
        )
        _ok("Virtual environment created")

    print("  Installing dependencies...")
    pip = str(_venv_pip())
    subprocess.run([pip, "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([pip, "install", "-q", "-r", REQUIREMENTS_FILE], check=True)
    _ok("Dependencies installed")


# ---------------------------------------------------------------------------
# .env configuration
# ---------------------------------------------------------------------------

def _validate_token(token):
    """Hit Webex /people/me to check the token. Returns bot name or None."""
    try:
        req = urllib.request.Request(
            WEBEX_ME_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("displayName", "(unknown)")
    except Exception:
        return None


def _prompt_token():
    """Ask for and validate a Webex bot token. Returns the token string."""
    print(f"  {BOLD}1. Create a Webex bot to get your token:{RESET}")
    print(f"     {DIM}{WEBEX_BOT_URL}{RESET}")
    print()

    try:
        webbrowser.open(WEBEX_BOT_URL)
        print(f"     {DIM}(Opened in your browser){RESET}")
        print()
    except Exception:
        pass

    while True:
        token = input("  Paste your Bot Access Token: ").strip()
        if not token:
            _err("Token cannot be empty.")
            continue

        print("  Validating...")
        name = _validate_token(token)
        if name:
            _ok(f"Token valid — bot name: {name}")
            return token

        _err("Token validation failed. Check that you copied the full token.")
        retry = input("  Try again? (y/n): ").strip().lower()
        if retry not in ("y", "yes"):
            sys.exit(1)


def _prompt_email():
    """Ask for the authorized Webex email."""
    print()
    print(f"  {BOLD}2. Your Webex email{RESET}")
    print("     Only this email will be allowed to use the bot.")
    print()

    while True:
        email = input("  Webex email: ").strip()
        if email and "@" in email:
            return email
        _err("Please enter a valid email address.")


def _setup_env(force=False):
    env_path = Path(ENV_FILE)

    if env_path.exists() and not force:
        _ok(".env file exists")
        resp = input("  Reconfigure? (y/n): ").strip().lower()
        if resp not in ("y", "yes"):
            return

    _heading("Configure your Webex bot")

    token = _prompt_token()
    email = _prompt_email()

    env_path.write_text(
        f"WEBEX_BOT_TOKEN={token}\n"
        f"WEBEX_USER_EMAIL={email}\n"
    )

    print()
    _ok(".env saved")


# ---------------------------------------------------------------------------
# Start the bot
# ---------------------------------------------------------------------------

def _start_bot():
    venv_python = str(_venv_python())
    script_dir = os.path.dirname(os.path.abspath(__file__)) or "."

    print(
        f"\n{BOLD}Starting Claude Webex Bridge...{RESET}\n"
        "  The bot will message you on Webex when it's ready.\n"
        "  Press Ctrl+C to stop.\n"
    )

    try:
        subprocess.run([venv_python, "bot.py"], cwd=script_dir)
    except KeyboardInterrupt:
        print(f"\n\n{BOLD}Bot stopped.{RESET}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

    force_setup = "--setup" in sys.argv

    _banner()

    _heading("Checking prerequisites")
    _check_python()
    if not _check_claude_cli():
        sys.exit(1)

    _heading("Setting up environment")
    _setup_venv()
    _setup_env(force=force_setup)

    _start_bot()


if __name__ == "__main__":
    main()
