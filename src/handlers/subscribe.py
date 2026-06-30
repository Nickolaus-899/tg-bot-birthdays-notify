"""
Handlers for /subscribe and /unsubscribe commands.
"""

from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.db import SUBSCRIBERS_FILE
from src.storage import read_json, write_json


async def subscribe_entry(message: Message, state: FSMContext) -> None:
    chat_id = message.chat.id
    subscribers: list = read_json(SUBSCRIBERS_FILE, default=[])

    if chat_id in subscribers:
        await message.answer("✅ Вы уже подписаны на уведомления о днях рождения в 8:00.")
        return

    subscribers.append(chat_id)
    write_json(SUBSCRIBERS_FILE, subscribers)
    await message.answer(
        "🎉 Вы успешно подписались на уведомления о днях рождения!\n"
        "Вы будете получать сообщения каждый день в 8:00, когда у кого-то день рождения."
    )


async def unsubscribe_entry(message: Message) -> None:
    chat_id = message.chat.id
    subscribers: list = read_json(SUBSCRIBERS_FILE, default=[])

    if chat_id not in subscribers:
        await message.answer("❌ Вы не подписаны на уведомления.")
        return

    subscribers.remove(chat_id)
    write_json(SUBSCRIBERS_FILE, subscribers)
    await message.answer("✅ Вы успешно отписались от уведомлений о днях рождения.")
