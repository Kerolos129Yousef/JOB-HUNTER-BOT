#!/usr/bin/env python3
"""JOB HUNTER BOT

Reads LinkedIn Job Alert emails from Gmail, filters them by keyword,
and sends new matches to Telegram — without ever repeating a job.

Usage:
    python main.py                 # normal run (use this in cron)
    python main.py --dry-run       # parse & filter, but don't send or record
    python main.py --test-telegram # send a test message to your chat
    python main.py --chat-id       # print recent chat ids (setup helper)
"""
from __future__ import annotations

import argparse
import logging
import sys

from config import config
from src.email_reader import EmailReader, decode_subject, extract_html
from src.filters import filter_jobs
from src.parser import parse_jobs
from src.storage import SeenStore
from src.telegram_notifier import TelegramNotifier


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


log = logging.getLogger("job-hunter")


def cmd_chat_id() -> int:
    """Print chat ids from recent updates, to help fill TELEGRAM_CHAT_ID."""
    if not config.telegram_bot_token:
        print("Set TELEGRAM_BOT_TOKEN in .env first.")
        return 1
    tg = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id or "0")
    data = tg.get_updates()
    if not data.get("ok"):
        print("Telegram error:", data)
        return 1
    results = data.get("result", [])
    if not results:
        print(
            "No updates yet. Open Telegram, send your bot any message, "
            "then run this again."
        )
        return 0
    print("Recent chats that messaged your bot:")
    seen: set[str] = set()
    for upd in results:
        chat = (upd.get("message") or upd.get("channel_post") or {}).get("chat", {})
        cid = str(chat.get("id", ""))
        if cid and cid not in seen:
            seen.add(cid)
            name = chat.get("title") or chat.get("username") or chat.get("first_name")
            print(f"  chat_id = {cid}   ({name})")
    return 0


def cmd_test_telegram() -> int:
    tg = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    tg.send_text("✅ JOB HUNTER BOT is connected. You'll get new jobs here.")
    print("Sent a test message to your Telegram chat.")
    return 0


def run(dry_run: bool = False) -> int:
    problems = config.validate()
    if problems and not dry_run:
        for p in problems:
            log.error("Config problem: %s", p)
        return 1

    all_jobs = []
    with EmailReader(
        config.imap_host,
        config.imap_port,
        config.imap_user,
        config.imap_password,
        config.imap_folder,
    ) as reader:
        for _uid, msg in reader.fetch_linkedin_emails(
            senders=config.linkedin_senders,
            since_days=config.search_days,
            mark_as_read=config.mark_as_read,
        ):
            subject = decode_subject(msg)
            html = extract_html(msg)
            jobs = parse_jobs(html)
            log.info("Email %r -> %d job(s)", subject[:60], len(jobs))
            all_jobs.extend(jobs)

    # De-duplicate across emails by job id.
    unique = {j.job_id: j for j in all_jobs}
    matched = filter_jobs(
        list(unique.values()), config.keywords, config.exclude_keywords
    )

    store = SeenStore(config.db_path)
    try:
        fresh = store.new_jobs(matched)
        log.info("%d new matching job(s) to send", len(fresh))

        if dry_run:
            for job in fresh:
                print(f"[DRY] {job.title} | {job.company} | {job.location}\n      {job.url}")
            return 0

        tg = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        for job in fresh:
            try:
                tg.send_job(job)
                store.mark_sent(job)
            except Exception:  # noqa: BLE001 - one bad send shouldn't stop the rest
                log.exception("Failed to send job %s", job.job_id)
    finally:
        store.close()
    return 0


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="JOB HUNTER BOT")
    parser.add_argument("--dry-run", action="store_true",
                        help="parse & filter but don't send or record")
    parser.add_argument("--test-telegram", action="store_true",
                        help="send a test message to your Telegram chat")
    parser.add_argument("--chat-id", action="store_true",
                        help="print chat ids from recent bot updates")
    args = parser.parse_args()

    if args.chat_id:
        return cmd_chat_id()
    if args.test_telegram:
        return cmd_test_telegram()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
