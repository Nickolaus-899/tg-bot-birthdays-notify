from src import router, dp
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.handlers.subscribe import subscribe_entry, unsubscribe_entry
from src.handlers.birthdays import router as birthday_router
from src.db import extract_user, is_admin, BIRTHDAYS_FILE
from src.storage import read_json


# ── cancel state (works in any active FSM state) ───────────────────────────────

class AnyState(StatesGroup):
    any = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нет активного действия для отмены.")
        return
    await state.clear()
    await message.answer("❌ Действие отменено.")


# ── basic commands ─────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 Привет! Я — бот для уведомлений о днях рождения.\n\n"
        "Используйте /help, чтобы узнать доступные команды."
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 Доступные команды:\n\n"
        "/subscribe — подписаться на уведомления о днях рождения\n"
        "/unsubscribe — отписаться от уведомлений\n"
        "/status — проверить статус подписки\n"
        "/list — показать список всех дней рождения\n\n"
        "👑 Команды для администраторов:\n"
        "/add — добавить день рождения\n"
        "/remove — удалить день рождения по ID\n"
    )


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, state: FSMContext) -> None:
    await subscribe_entry(message, state)


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message) -> None:
    await unsubscribe_entry(message)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if extract_user(key="chat_id", value=message.chat.id):
        await message.answer("✅ Вы подписаны на уведомления о днях рождения.")
    else:
        await message.answer(
            "❌ Вы не подписаны на уведомления.\n"
            "Используйте /subscribe, чтобы подписаться."
        )


@router.message(Command("getid"))
async def cmd_start(message: Message) -> None:
    await message.answer(f"ID твоего чата {message.chat.id}")



MONTH_NAMES = {
    1: ("Январь", "❄️"), 2: ("Февраль", "🌨️"), 3: ("Март", "🌱"),
    4: ("Апрель", "🌸"), 5: ("Май", "🌻"), 6: ("Июнь", "☀️"),
    7: ("Июль", "🏖️"), 8: ("Август", "🍉"), 9: ("Сентябрь", "🍂"),
    10: ("Октябрь", "🎃"), 11: ("Ноябрь", "🌧️"), 12: ("Декабрь", "🎄")
}

@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    birthdays: dict = read_json(BIRTHDAYS_FILE, default={})
    if not birthdays:
        await message.answer("📭 Список дней рождения пуст.")
        return

    admin = is_admin(message.from_user.id)

    by_month: dict[int, list] = {}
    for bid, entry in birthdays.items():
        month, day = entry["birthday"].split("-")
        month, day = int(month), int(day)
        by_month.setdefault(month, []).append((day, bid, entry["name"]))

    lines = ["🎂 Список дней рождения:\n"]
    for month_num in sorted(by_month.keys()):
        name_str, emoji = MONTH_NAMES[month_num]
        lines.append(f"{emoji} *{name_str}*")
        for day, bid, name in sorted(by_month[month_num]):
            if admin:
                lines.append(f"  {day} {name} — ID: {bid}")
            else:
                lines.append(f"  {day} {name}")
        lines.append("")

    await message.answer("\n".join(lines).strip(), parse_mode="Markdown")


# ── wire everything into the dispatcher ───────────────────────────────────────

dp.include_router(birthday_router)
dp.include_router(router)
