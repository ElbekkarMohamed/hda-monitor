# HDA Meldungs-Monitor

Automated notification system for the Hochschule Darmstadt (h_da) student
portal. The portal shows exam changes and announcements ("Meldungen") but
sends no email or push notification, so they are easy to miss. This tool
checks the portal on a schedule and forwards any new message to an n8n
workflow, which sends an email.

## How it works

1. A Python script (Playwright) logs into the h_da portal headlessly.
2. It opens the notification infobox and reads the newest message.
3. It hashes the message and compares it to the last seen hash.
4. If the message is new, it POSTs the text to an n8n webhook.
5. n8n sends the message to my inbox via Gmail.
6. Windows Task Scheduler runs the script on a schedule.

## Tech stack

- Python, Playwright (browser automation)
- n8n (workflow automation, webhook to Gmail)
- Windows Task Scheduler (scheduling)
- SHA-256 hashing for change detection

## Setup

Set the required environment variables:

    HDA_USER      your portal username
    HDA_PASS      your portal password
    HDA_WEBHOOK   your n8n webhook URL

Install dependencies:

    pip install playwright requests
    playwright install chromium

Run:

    python hda_monitor.py

## Notes

Credentials are read from environment variables and are never stored in
the repository. The portal HTML changes occasionally; when a selector
breaks, run with headless=False to see which step fails.
