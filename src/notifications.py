"""
Birthday notification scheduler.

Runs a daily check at 10:00 (server local time).
Sends a message to every subscribed chat when it's someone's birthday today.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src import bot
from src.db import BIRTHDAYS_FILE, SUBSCRIBERS_FILE
from src.storage import read_json

logger = logging.getLogger(__name__)


async def check_birthdays() -> None:
    """Check today's date against all stored birthdays and notify subscribers."""
    today = datetime.now()
    today_key = f"{today.month:02d}-{today.day:02d}"  # MM-DD

    birthdays: dict = read_json(BIRTHDAYS_FILE, default={})
    subscribers: list = read_json(SUBSCRIBERS_FILE, default=[])

    celebrants = [
        entry["name"]
        for entry in birthdays.values()
        if entry.get("birthday") == today_key
    ]

    if not celebrants or not subscribers:
        return

    for name in celebrants:
        text = f"🎂 Сегодня {name} празднует свой день рождения!🎉🥳"
        for chat_id in subscribers:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.warning("Cannot send msg %s: %s", chat_id, e)


def start_scheduler() -> AsyncIOScheduler:
    """Create and start the APScheduler instance. Returns the scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_birthdays,
        trigger=CronTrigger(hour=5, minute=0),
        id="birthday_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler is started (daily at 8:00).")
    return scheduler
