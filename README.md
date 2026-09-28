# 🎯 JOB HUNTER BOT

Watches your Gmail for **LinkedIn Job Alert** emails, keeps only the jobs that
match your keywords (DevOps / SRE / Platform / Cloud / Infrastructure …), and
pushes each new one to you on **Telegram** — no duplicates, ever.

```
LinkedIn Job Alert email  ──►  Gmail (IMAP)  ──►  parse + filter  ──►  Telegram
                                                        │
                                                   seen_jobs.db  (dedup)
```

Why this design? LinkedIn has **no public jobs API**, and scraping the site
risks a ban. LinkedIn's own Job Alert emails are the safe, official feed — this
bot just reads them for you and forwards the matches.

---

## 1. Set up the LinkedIn Job Alerts

On LinkedIn, search for each role you want and turn on the **Job Alert** toggle
(set it to **email**, ideally daily/instant). Suggested searches:

- `DevOps Engineer`
- `Site Reliability Engineer (SRE)`
- `Platform Engineer`
- `Cloud Engineer`
- `Infrastructure Engineer`

LinkedIn will now email you when new jobs appear.

## 2. Set up Gmail (App Password)

The bot reads email over IMAP. For Gmail you need an **App Password**:

1. Enable **2-Step Verification** on your Google account.
2. Go to **Google Account → Security → App passwords**.
3. Create one for "Mail" and copy the 16-character code.

> Tip: create a Gmail **filter** that routes `from:linkedin.com` alerts into a
> label (e.g. `LinkedIn`), then set `IMAP_FOLDER=LinkedIn` for faster runs.

## 3. Create the Telegram bot

1. In Telegram, message **@BotFather** → `/newbot` → copy the **token**.
2. Open a chat with your new bot and send it any message (e.g. "hi").
3. Get your chat id (after step 4 below): `python main.py --chat-id`.

## 4. Install & configure

```bash
cd JOB-HUNTER-BOT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in IMAP + Telegram values
```

Discover your Telegram chat id and fill it into `.env`:

```bash
python main.py --chat-id
```

Test the Telegram connection:

```bash
python main.py --test-telegram
```

## 5. Run it

```bash
# See what it would send, without sending or recording anything:
python main.py --dry-run

# Real run (sends new jobs to Telegram):
python main.py
```

## 6. Run it automatically (cron)

Poll every 15 minutes:

```bash
chmod +x run.sh
crontab -e
```

Add this line (use the absolute path to the project):

```cron
*/15 * * * * /home/braveboy911/Downloads/JOB-HUNTER-BOT/run.sh
```

Logs go to `job-hunter.log` in the project folder.

---

## Configuration reference

All settings live in `.env` (see `.env.example` for the full list):

| Variable | What it does |
|---|---|
| `IMAP_USER` / `IMAP_PASSWORD` | Gmail address + **App Password** |
| `IMAP_FOLDER` | Mailbox to read (`INBOX` or a label) |
| `SEARCH_DAYS` | Only scan emails from the last N days |
| `KEYWORDS` | Keep jobs whose title matches ANY of these |
| `EXCLUDE_KEYWORDS` | Drop jobs whose title matches ANY of these |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Where to send jobs |

## Project layout

```
main.py                    Orchestrator + CLI
config.py                  Loads .env into a validated Config
src/email_reader.py        Gmail IMAP reader
src/parser.py              LinkedIn email HTML -> Job objects
src/filters.py             Keyword include/exclude
src/storage.py             SQLite dedup store
src/telegram_notifier.py   Telegram Bot API sender
src/models.py              The Job dataclass
```

## Notes & limitations

- Parsing LinkedIn's email HTML is **heuristic**; LinkedIn changes its markup
  from time to time. Titles and links are robust; company/location are
  best-effort. If a field is missing the job is still sent.
- The bot never sends the same job twice (tracked by LinkedIn job id in
  `seen_jobs.db`). Delete that file to reset.
- Keep `.env` and `*.db` out of git — they're already in `.gitignore`.
