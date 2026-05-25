"""
Central definition of data-file paths and DB initialisation.
"""

import os
from src.storage import read_json, write_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

BIRTHDAYS_FILE = os.path.join(DATA_DIR, "birthdays.json")
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "subscribers.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
COUNTER_FILE = os.path.join(DATA_DIR, "counter.json")


def init_db(admin_id: int | None = None) -> None:
    """
    Ensure all data files exist with sensible defaults.
    If *admin_id* is provided and the admins list is empty, that ID is added
    as the first admin. Pass your own Telegram user ID here from main.py.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # birthdays: { "1": { "name": "...", "birthday": "MM-DD" }, ... }
    if not os.path.exists(BIRTHDAYS_FILE):
        write_json(BIRTHDAYS_FILE, {})

    # subscribers: [ chat_id, ... ]
    if not os.path.exists(SUBSCRIBERS_FILE):
        write_json(SUBSCRIBERS_FILE, [])

    # admins: [ telegram_user_id, ... ]
    if not os.path.exists(ADMINS_FILE):
        initial_admins = [admin_id] if admin_id else []
        write_json(ADMINS_FILE, initial_admins)

    # counter: { "next_id": 1 }
    if not os.path.exists(COUNTER_FILE):
        write_json(COUNTER_FILE, {"next_id": 1})


# ── convenience helpers ────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    admins = read_json(ADMINS_FILE, default=[])
    return user_id in admins


def extract_user(key: str, value) -> bool:
    """Return True if a subscriber record with the given key=value exists."""
    subscribers = read_json(SUBSCRIBERS_FILE, default=[])
    if key == "chat_id":
        return value in subscribers
    return False
