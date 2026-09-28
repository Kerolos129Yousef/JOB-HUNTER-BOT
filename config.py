"""Central configuration, loaded from environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split(value: str) -> list[str]:
    """Split a comma-separated env value into a clean, lowercased list."""
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    # Gmail / IMAP
    imap_host: str = os.getenv("IMAP_HOST", "imap.gmail.com")
    imap_port: int = int(os.getenv("IMAP_PORT", "993"))
    imap_user: str = os.getenv("IMAP_USER", "")
    imap_password: str = os.getenv("IMAP_PASSWORD", "")
    imap_folder: str = os.getenv("IMAP_FOLDER", "INBOX")
    search_days: int = int(os.getenv("SEARCH_DAYS", "3"))
    mark_as_read: bool = _bool(os.getenv("MARK_AS_READ", "false"))

    linkedin_senders: list[str] = field(
        default_factory=lambda: _split(
            os.getenv(
                "LINKEDIN_SENDERS",
                "jobalerts-noreply@linkedin.com,jobs-noreply@linkedin.com,"
                "jobs-listings@linkedin.com",
            )
        )
    )

    # Filtering
    keywords: list[str] = field(
        default_factory=lambda: _split(os.getenv("KEYWORDS", ""))
    )
    exclude_keywords: list[str] = field(
        default_factory=lambda: _split(os.getenv("EXCLUDE_KEYWORDS", ""))
    )

    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Local state
    db_path: str = os.getenv("DB_PATH", "seen_jobs.db")

    def validate(self) -> list[str]:
        """Return a list of human-readable problems (empty == all good)."""
        problems: list[str] = []
        if not self.imap_user:
            problems.append("IMAP_USER is not set")
        if not self.imap_password:
            problems.append("IMAP_PASSWORD is not set (use a Gmail App Password)")
        if not self.telegram_bot_token:
            problems.append("TELEGRAM_BOT_TOKEN is not set")
        if not self.telegram_chat_id:
            problems.append("TELEGRAM_CHAT_ID is not set")
        if not self.keywords:
            problems.append("KEYWORDS is empty — nothing would ever match")
        return problems


config = Config()
