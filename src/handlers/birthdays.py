"""
Admin-only handlers for /add and /remove commands.

/add  — multi-step FSM: asks for name, then date (DD.MM or DD.MM.YYYY)
/remove — asks for the ID to delete
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from src.db import BIRTHDAYS_FILE, COUNTER_FILE, is_admin, get_owner
from src.storage import read_json, write_json

router = Router()

# ── FSM states ─────────────────────────────────────────────────────────────────

class AddBirthdayStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()


class RemoveBirthdayStates(StatesGroup):
    waiting_for_id = State()


# ── helpers ────────────────────────────────────────────────────────────────────

def _next_id() -> int:
    counter = read_json(COUNTER_FILE, default={"next_id": 1})
    current = counter.get("next_id", 1)
    counter["next_id"] = current + 1
    write_json(COUNTER_FILE, counter)
    return current


def _parse_date(raw: str) -> str | None:
    """
    Accept DD.MM or DD.MM.YYYY and normalise to MM-DD.
    Returns None if the input cannot be parsed.
    """
    raw = raw.strip()
    parts = raw.split(".")
    if len(parts) < 2:
        return None
    try:
        day = int(parts[0])
        month = int(parts[1])
    except ValueError:
        return None
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    return f"{month:02d}-{day:02d}"


# ── /add ───────────────────────────────────────────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("🚫 У вас нет прав для выполнения этой команды.")
        return

    await state.set_state(AddBirthdayStates.waiting_for_name)
    await message.answer(
        "➕ Добавление дня рождения.\nВведите имя (например: Иван Иванов):\n\nДля отмены нажмите /cancel"
    )


@router.message(AddBirthdayStates.waiting_for_name)
async def add_get_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()

    if name == "/cancel":
        await message.answer("Операция отменена")
        await state.clear()
        return

    if not name:
        await message.answer("❌ Имя не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(name=name)
    await state.set_state(AddBirthdayStates.waiting_for_date)
    await message.answer(
        f"📅 Введите дату рождения для «{name}» в формате ДД.ММ\n"
        "(например: 25.05):\n\n"
        "Для отмены нажмите /cancel"
    )


@router.message(AddBirthdayStates.waiting_for_date)
async def add_get_date(message: Message, state: FSMContext) -> None:
    if message.text.strip() == "/cancel":
        await message.answer("Операция отменена")
        await state.clear()
        return

    date_str = _parse_date(message.text)
    if not date_str:
        await message.answer(
            "❌ Неверный формат даты. Введите дату в формате ДД.ММ или ДД.ММ.ГГГГ\n\n"
            "(например: 25.05):\n\n"
            "Для отмены нажмите /cancel"
        )
        return

    data = await state.get_data()
    name = data["name"]
    new_id = _next_id()

    birthdays = read_json(BIRTHDAYS_FILE, default={})
    birthdays[str(new_id)] = {"name": name, "birthday": date_str}
    write_json(BIRTHDAYS_FILE, birthdays)

    await state.clear()

    day, month = date_str.split("-")[1], date_str.split("-")[0]
    await message.answer(
        f"✅ День рождения добавлен!\n\n"
        f"🆔 ID: {new_id}\n"
        f"👤 Имя: {name}\n"
        f"🎂 Дата: {day}.{month}"
    )

    msg_for_owner = f"Админ добавил новый день рождения:\n[{new_id}] {name}"
    await notify_owner(msg_for_owner, message)


# ── /remove ────────────────────────────────────────────────────────────────────

@router.message(Command("remove"))
async def cmd_remove(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("🚫 У вас нет прав для выполнения этой команды.")
        return

    birthdays = read_json(BIRTHDAYS_FILE, default={})
    if not birthdays:
        await message.answer("📭 Список дней рождения пуст.")
        return

    lines = ["📋 Список дней рождения:\n"]
    for bid, entry in sorted(birthdays.items(), key=lambda x: int(x[0])):
        month, day = entry["birthday"].split("-")
        lines.append(f"  [{bid}] {entry['name']} — {day}.{month}")
    lines.append("\nВведите ID записи, которую хотите удалить:\n\nДля отмены нажмите /cancel")

    await state.set_state(RemoveBirthdayStates.waiting_for_id)
    await message.answer("\n".join(lines))


@router.message(RemoveBirthdayStates.waiting_for_id)
async def remove_get_id(message: Message, state: FSMContext) -> None:
    raw_id = message.text.strip()
    if raw_id == "/cancel":
        await message.answer("Операция отменена")
        await state.clear()
        return


    birthdays = read_json(BIRTHDAYS_FILE, default={})

    if raw_id not in birthdays:
        await message.answer(
            f"❌ Запись с ID {raw_id} не найдена. Введите корректный ID или /cancel:"
        )
        return

    entry = birthdays.pop(raw_id)
    write_json(BIRTHDAYS_FILE, birthdays)

    await state.clear()
    month, day = entry["birthday"].split("-")
    await message.answer(
        f"✅ Запись удалена.\n\n"
        f"👤 Имя: {entry['name']}\n"
        f"🎂 Дата: {day}.{month}"
    )

    msg_for_owner = f"Админ удалил день рождения:\n[{raw_id}] {entry['name']}"
    await notify_owner(msg_for_owner, message)


async def notify_owner(text: str, message: Message) -> None:
    owner_id = get_owner()
    await message.bot.send_message(owner_id, f"{message.from_user.full_name} (ID: {message.from_user.id}):\n\n{text}")
