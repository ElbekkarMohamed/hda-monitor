from playwright.sync_api import sync_playwright
import hashlib
import os
import requests
import time
import sys

# =========================
# CONFIG
# =========================
USERNAME = os.environ["HDA_USER"]
PASSWORD = os.environ["HDA_PASS"]
WEBHOOK_URL = os.environ.get("HDA_WEBHOOK" , "http://localhost:5678/webhook/hda-meldung")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HASH_FILE = os.path.join(BASE_DIR, "last_hash.txt")

# =========================
# HELPERS
# =========================
def get_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_last_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return None

def save_hash(h):
    with open(HASH_FILE, "w") as f:
        f.write(h)

# =========================
# MAIN
# =========================
browser = None
try:
    print("Starting HDA monitor...")
    with sync_playwright() as p:
        # headless=False so you can watch. Change to True for Task Scheduler.
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(
            "https://my.h-da.de/qisserver/pages/cs/sys/portal/hisinoneStartPage.faces",
            timeout=30000
        )
        page.wait_for_load_state("networkidle")

        # --- LOGIN ---
        # Open the login popup
        page.get_by_text("Zur Anmeldung").first.click()
        page.wait_for_timeout(2000)

        # Fields live in the popup's containers (avoids hidden duplicates)
        page.locator("div.accountContainer input[type='text']").fill(USERNAME)
        page.locator("div.passwordContainer input[type='password']").fill(PASSWORD)
        page.get_by_role("button", name="Login").click()
        page.wait_for_load_state("networkidle")
        print("Logged in.")

        # --- OPEN NOTIFICATION BELL ---
        # Bell is a <button> whose id contains collapsibleHeaderActionFrom:infobox
        page.locator('button[id*="collapsibleHeaderActionFrom:infobox"]').click()
        page.wait_for_timeout(3000)

        # --- READ MESSAGES (don't crash if empty) ---
        messages = page.locator(".portalMessageText")
        count = messages.count()
        print(f"Found {count} message(s).")

        if count == 0:
            print("No messages in infobox right now.")
            sys.exit(0)

        # FIRST message = newest
        latest_message = messages.first.inner_text().strip()
        current_hash = get_hash(latest_message)
        last_hash = load_last_hash()

        if current_hash != last_hash:
            print("\nNEW MESSAGE DETECTED:\n")
            print(latest_message)
            try:
                response = requests.post(
                    WEBHOOK_URL,
                    json={
                        "message": latest_message,
                        "timestamp": time.time()
                    },
                    timeout=10
                )
                response.raise_for_status()
                save_hash(current_hash)
                print("Webhook sent successfully and hash saved.")
            except requests.RequestException as e:
                print("Webhook failed — hash NOT saved:")
                print(e)
        else:
            print("No new messages.")

except Exception as e:
    print("Script crashed:")
    print(e)
finally:
    if browser:
        try:
            browser.close()
        except:
            pass
    print("Script finished.")