import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

WEBEX_BOT_TOKEN: str = os.environ["WEBEX_BOT_TOKEN"]
WEBEX_USER_EMAIL: str = os.environ["WEBEX_USER_EMAIL"]

WEBEX_BASE_URL: str = "https://webexapis.com/v1"
WEBEX_MAX_MESSAGE_BYTES: int = 7000
POLL_INTERVAL_SECONDS: float = 2.5

# Shared constants — names must match what sessions.py and claude_cli.py import
CLAUDE_HISTORY_FILE: Path = Path.home() / ".claude" / "history.jsonl"
CLAUDE_PROJECTS_DIR: Path = Path.home() / ".claude" / "projects"
MAX_SESSIONS_DISPLAYED: int = 10
CLI_TIMEOUT_SECONDS: int = 300  # 5 minutes
