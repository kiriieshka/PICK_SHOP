from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from bot.keyboards.admin import admin_menu
from bot.database.db import generate_keys

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "👨‍💼 АДМИН-ПАНЕЛЬ\n\n"
        "Здесь можно бесплатно создать ключ доступа для теста, себя или друга.",
        reply_markup=admin_menu(),
    )


@router.callback_query(F.data == "admin:generate")
async def generate(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Нет доступа.", show_alert=True)
        return

    codes = await generate_keys(1)
    code = codes[0]

    await c.message.edit_text(
        "✅ Ключ создан\n\n"
        f"🔑 <code>{code}</code>\n\n"
        "Ключ можно передать себе или другу. Покупка для него не требуется.",
        parse_mode="HTML",
        reply_markup=admin_menu(),
    )
    await c.answer("Ключ создан")
