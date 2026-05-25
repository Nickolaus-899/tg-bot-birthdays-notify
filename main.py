import asyncio
import logging

from src import bot, dp
from src.db import init_db
from src.notifications import start_scheduler

MY_TELEGRAM_ID: int = 753442299
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import src.main_router  # noqa: F401, E402  — registers all handlers


async def main() -> None:
    init_db(admin_id=MY_TELEGRAM_ID)
    scheduler = start_scheduler()

    try:
        print("Waiting for the commands...")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    print("Running bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping...")
