# Claude Webex Bridge

Resume and interact with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) sessions from Webex Teams.

## Prerequisites

- **Python 3.9+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** installed and on your PATH (`claude --version` should work)
- At least one prior Claude Code session (the bot reads from `~/.claude/history.jsonl`)

## Quick Start

### 1. Create a Webex Bot

1. Go to [developer.webex.com](https://developer.webex.com) and sign in
2. Avatar menu -> "My Webex Apps" -> "Create a New App" -> "Create a Bot"
3. Fill in bot name and username, click "Add Bot"
4. Copy the Bot Access Token (shown only once)

### 2. Run Setup Script

```bash
./setup.sh
```

The setup script will:
- Create a virtual environment
- Install dependencies
- Prompt for your bot token and email
- Create the `.env` file

### 3. Create 1:1 Room

In Webex, search for your bot's username and send it any message to create the direct room.

### 4. Start the Bot

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
| `/sessions` | List recent sessions as a numbered list |
| `/connect N` | Connect to session N from the list |
| `/disconnect` | Disconnect from current session |
| `/status` | Show connection status and permission mode |
| `/safe` | Toggle permission mode (skip-permissions / safe) |

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

- `webex-bot` (websocket library) requires Python 3.10+ — system Python is 3.9
- Webhooks require a public URL (ngrok, etc.) — unnecessary for a personal bot
- Polling via `httpx` works on Python 3.9, needs no public URL, and adds ~2.5s latency (negligible when CLI calls take seconds-to-minutes)

### Key Design Decisions

- **Session discovery** reads Claude Code's own history and project files — no separate database needed.
- **Numbered session list** + `/connect N` replaces Telegram's inline keyboard buttons (Webex doesn't have an equivalent).
- **Byte-aware message splitting** respects Webex's 7,439-byte message limit by splitting on UTF-8 byte length, not character count.
- **"Thinking..." pattern** sends a placeholder message, then edits it with the first response chunk (falls back to a new message if the edit fails).
- **Concurrency guard** prevents overlapping CLI calls — a second message while one is processing gets a "still processing" reply.
- **Rate-limit handling** retries on 429 responses using the `Retry-After` header, up to 3 times.
- **Permission modes**: `skip-permissions` (default) auto-approves tool use. `safe` mode respects approval prompts, but `--print` mode cannot show interactive prompts, so this may cause the CLI to hang.
- **CLI timeout** kills the process after 5 minutes to prevent runaway sessions.

### Shared Modules

`sessions.py` and `claude_cli.py` are shared verbatim with [claude-telegram-bridge](../claude-telegram-bridge/). They import constants from `config.py`, which each project defines independently.

## Security

Only the email matching `WEBEX_USER_EMAIL` (case-insensitive) can interact with the bot. Messages from other users are silently ignored and logged as warnings.
