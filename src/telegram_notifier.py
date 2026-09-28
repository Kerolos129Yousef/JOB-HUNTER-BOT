"""Send job notifications to Telegram via the Bot API."""
from __future__ import annotations

import html
import logging

import requests

from .models import Job

log = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, timeout: int = 20) -> None:
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout

    def _post(self, method: str, payload: dict) -> dict:
        url = _API.format(token=self.token, method=method)
        resp = requests.post(url, json=payload, timeout=self.timeout)
        data = resp.json()
        if not data.get("ok"):
            log.error("Telegram %s failed: %s", method, data)
            resp.raise_for_status()
        return data

    def send_job(self, job: Job) -> None:
        parts = [f"<b>{html.escape(job.title)}</b>"]
        if job.company:
            parts.append(f"🏢 {html.escape(job.company)}")
        if job.location:
            parts.append(f"📍 {html.escape(job.location)}")
        parts.append(f'🔗 <a href="{html.escape(job.url)}">View on LinkedIn</a>')
        text = "\n".join(parts)

        self._post(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )
        log.info("Sent job to Telegram: %s", job.title)

    def send_text(self, text: str) -> None:
        self._post("sendMessage", {"chat_id": self.chat_id, "text": text})

    def get_updates(self) -> dict:
        """Helper for discovering your chat id (see main.py --chat-id)."""
        url = _API.format(token=self.token, method="getUpdates")
        return requests.get(url, timeout=self.timeout).json()
