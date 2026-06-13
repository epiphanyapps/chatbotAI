#!/usr/bin/env python3
"""
Multi-Personality Intimate AI Bot — Telegram channel.

This is now a THIN CLIENT. All inference, persona voice, and conversation memory
live in the backend conversation engine (``backend/app/engine``) and are reached
through ``POST /chat/message``. The web app and this bot therefore share one
brain — same model, same Sophia, same memory — instead of the old, dead TF-IDF
matcher that used to live here.

The bot's only jobs: long-poll Telegram, forward user text to the backend, and
deliver the returned reply as paced, multi-bubble "texting".

Note (TELE-02, deferred to v2): mapping a Telegram user to their IntimateAI
account is not yet implemented. Set ``INTIMATEAI_API_TOKEN`` to an age-verified
user's access token to drive a single account end-to-end for now.
"""

import logging
import os
import random
import time

import requests

# Configuration — all via environment variables.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
API_URL = os.getenv("INTIMATEAI_API_URL", "http://localhost:8080").rstrip("/")
API_TOKEN = os.getenv("INTIMATEAI_API_TOKEN", "")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TelegramBridge:
    """Forwards Telegram messages to the IntimateAI backend and relays replies."""

    def __init__(self) -> None:
        self.offset = 0

    # --- Backend -----------------------------------------------------------
    def fetch_reply(self, text: str) -> list[str]:
        """Call the backend; return the reply as a list of text bubbles."""
        try:
            resp = requests.post(
                f"{API_URL}/chat/message",
                json={"text": text},
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("bubbles", []) or ["..."]
        except requests.RequestException as exc:
            logger.error(f"Backend call failed: {exc}")
            return ["Mmm, give me a sec, baby…"]

    # --- Telegram I/O ------------------------------------------------------
    def send_typing(self, chat_id: int) -> None:
        try:
            requests.post(
                f"{TELEGRAM_API}/sendChatAction",
                data={"chat_id": chat_id, "action": "typing"},
                timeout=5,
            )
        except requests.RequestException:
            pass

    def send_text(self, chat_id: int, text: str) -> None:
        try:
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                data={"chat_id": chat_id, "text": text},
                timeout=10,
            )
        except requests.RequestException:
            pass

    def deliver(self, chat_id: int, bubbles: list[str]) -> None:
        """Send each bubble with a typing indicator and human-like pacing."""
        for bubble in bubbles:
            self.send_typing(chat_id)
            time.sleep(random.uniform(1.5, 3.5))
            self.send_text(chat_id, bubble)

    # --- Loop --------------------------------------------------------------
    def poll(self) -> list[dict]:
        try:
            resp = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params={"offset": self.offset, "timeout": 30},
                timeout=40,
            )
            resp.raise_for_status()
            return resp.json().get("result", [])
        except requests.RequestException as exc:
            logger.error(f"getUpdates failed: {exc}")
            time.sleep(3)
            return []

    def run(self) -> None:
        logger.info("🚀 Telegram bridge starting — backend: %s", API_URL)
        while True:
            for update in self.poll():
                self.offset = update["update_id"] + 1
                message = update.get("message") or {}
                text = message.get("text", "").strip()
                chat_id = message.get("chat", {}).get("id")
                if not text or chat_id is None:
                    continue
                # Never log message content — this is intimate adult content.
                # Log only ops metadata.
                logger.info("💬 chat_id=%s len=%d", chat_id, len(text))
                bubbles = self.fetch_reply(text)
                self.deliver(chat_id, bubbles)


if __name__ == "__main__":
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set TELEGRAM_BOT_TOKEN environment variable")
        raise SystemExit(1)
    if not API_TOKEN:
        logger.error("❌ Please set INTIMATEAI_API_TOKEN (age-verified user token)")
        raise SystemExit(1)
    TelegramBridge().run()
