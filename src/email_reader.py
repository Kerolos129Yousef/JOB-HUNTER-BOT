"""Read LinkedIn Job Alert emails from Gmail over IMAP."""
from __future__ import annotations

import email
import imaplib
import logging
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from typing import Iterator

log = logging.getLogger(__name__)


class EmailReader:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        folder: str = "INBOX",
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.folder = folder
        self._conn: imaplib.IMAP4_SSL | None = None

    # ---- connection -------------------------------------------------
    def __enter__(self) -> "EmailReader":
        self._conn = imaplib.IMAP4_SSL(self.host, self.port)
        self._conn.login(self.user, self.password)
        self._conn.select(self.folder)
        log.info("Connected to %s as %s (folder=%s)", self.host, self.user, self.folder)
        return self

    def __exit__(self, *_exc) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001 - closing is best-effort
                pass
            self._conn.logout()
            self._conn = None

    # ---- fetching ---------------------------------------------------
    def fetch_linkedin_emails(
        self,
        senders: list[str],
        since_days: int = 3,
        mark_as_read: bool = False,
    ) -> Iterator[tuple[bytes, Message]]:
        """Yield (uid, parsed message) for LinkedIn alert emails.

        IMAP SEARCH does not support OR across many senders cleanly on every
        server, so we search once per sender and merge the resulting UIDs.
        """
        assert self._conn is not None, "use EmailReader as a context manager"

        since = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        seen_uids: set[bytes] = set()

        for sender in senders:
            typ, data = self._conn.search(None, "FROM", f'"{sender}"', "SINCE", since)
            if typ != "OK":
                log.warning("IMAP search failed for sender %s", sender)
                continue
            uids = data[0].split()
            log.info("Found %d email(s) from %s", len(uids), sender)
            for uid in uids:
                if uid in seen_uids:
                    continue
                seen_uids.add(uid)
                msg = self._fetch_message(uid, mark_as_read=mark_as_read)
                if msg is not None:
                    yield uid, msg

    def _fetch_message(self, uid: bytes, mark_as_read: bool) -> Message | None:
        assert self._conn is not None
        # BODY.PEEK[] fetches without setting the \Seen flag.
        typ, data = self._conn.fetch(uid, "(BODY.PEEK[])")
        if typ != "OK" or not data or not isinstance(data[0], tuple):
            log.warning("Failed to fetch email uid=%s", uid)
            return None
        msg = email.message_from_bytes(data[0][1])
        if mark_as_read:
            self._conn.store(uid, "+FLAGS", "\\Seen")
        return msg


def decode_subject(msg: Message) -> str:
    raw = msg.get("Subject", "")
    parts = decode_header(raw)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def extract_html(msg: Message) -> str:
    """Return the best available HTML (or plain-text) body of the message."""
    html_body = ""
    text_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ctype == "text/html":
                html_body += decoded
            elif ctype == "text/plain":
                text_body += decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = decoded
            else:
                text_body = decoded
    return html_body or text_body
