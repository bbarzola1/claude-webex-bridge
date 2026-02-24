# Claude Webex Bridge

Resume and interact with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) sessions from Webex Teams.

## Prerequisites

- **Python 3.9+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** installed and on your PATH (`claude --version` should work)
- At least one prior Claude Code session (the bot reads from `~/.claude/history.jsonl`)

## Quick Start

```bash
cd claude-webex-bridge
python3 run.py
```

That's it. The script checks prerequisites, creates a virtual environment, installs dependencies, walks you through Webex bot token setup, and starts the bot. On subsequent runs it skips setup and goes straight to launch.

> **macOS note:** You can also double-click `Run.command`, but macOS Gatekeeper may block it. If that happens, just use `python3 run.py` from Terminal instead.

### Alternative: Step-by-Step Setup

If you prefer to set things up manually:

#### 1. Create a Webex Bot

1. Go to [developer.webex.com](https://developer.webex.com) and sign in
2. Avatar menu -> "My Webex Apps" -> "Create a New App" -> "Create a Bot"
3. Fill in bot name and username, click "Add Bot"
4. Copy the Bot Access Token (shown only once)

#### 2. Run Setup Script

```bash
./setup.sh
```

#### 3. Start the Bot

```bash
./start.sh
```

The bot runs in the background. Use these commands to manage it:

```bash
./status.sh   # Check if bot is running
./logs.sh     # View recent logs
./logs.sh -f  # Follow logs in real-time
./stop.sh     # Stop the bot
./restart.sh  # Restart the bot
```

## Manual Setup

If you prefer not to use the automated scripts:

<details>
<summary>Click to expand manual setup instructions</summary>

### 1. Create `.env` file

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
WEBEX_BOT_TOKEN=your-bot-access-token
WEBEX_USER_EMAIL=your-email@example.com
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Run Manually

```bash
python3 bot.py
```

You should see `Bot authenticated as: ...` in the logs.

</details>

## Commands

| Command | Description |
|---|---|
| `/start` or `/help` | Welcome message with available commands |
| `/new [dir]` | Start a new session (defaults to home directory) |
| `/sessions` | List recent sessions as a numbered list |
| `/resume N` | Resume session N from the list |
| `/resume` | Quick-resume the most recent session |
| `/disconnect` | Disconnect from current session |
| `/status` | Show connection status and permission mode |
| `/safe` | Toggle permission mode (skip-permissions / safe) |
| `/cancel` | Cancel a running command |

Connect to a session, then send plain text messages to interact with Claude Code.

## Architecture

```
bot.py          # Polling loop + command dispatch + message relay
webex_api.py    # Async httpx wrapper for Webex REST API
auth.py         # Email-based authorization check
config.py       # Environment variables + constants
sessions.py     # Claude Code session discovery (reads ~/.claude/history.jsonl)
claude_cli.py   # Async wrapper around the `claude` CLI
```

### Why Polling

- Polling keeps the minimum Python version at 3.9 (`webex-bot` websocket library requires 3.10+)
- No public URL needed (webhooks require ngrok or similar — unnecessary for a personal bot)
- ~2.5s latency is negligible when CLI calls take seconds-to-minutes

### Key Design Decisions

- **Session discovery** reads Claude Code's own history and project files — no separate database needed.
- **Numbered session list** + `/resume N` replaces Telegram's inline keyboard buttons (Webex doesn't have an equivalent).
- **Byte-aware message splitting** respects Webex's 7,439-byte message limit by splitting on UTF-8 byte length, not character count.
- **"Thinking..." pattern** sends a placeholder message, then edits it with the first response chunk (falls back to a new message if the edit fails).
- **Concurrency guard** prevents overlapping CLI calls — a second message while one is processing gets a "still processing" reply.
- **Rate-limit handling** retries on 429 responses using the `Retry-After` header, up to 3 times.
- **Permission modes**: `safe` (default) respects approval prompts. `skip-permissions` mode auto-approves tool use. Toggle with `/safe`. Note: in safe mode, `--print` cannot show interactive prompts, so the CLI may hang on approval requests — use `/safe` to switch to skip-permissions if this happens.
- **CLI timeout** kills the process after 5 minutes to prevent runaway sessions.

### Shared Modules

`sessions.py` and `claude_cli.py` are designed to be reusable across different chat platform bridges. They import constants from `config.py`, which each project defines independently.

## Security

Only the email matching `WEBEX_USER_EMAIL` (case-insensitive) can interact with the bot. Messages from other users are silently ignored and logged as warnings.
