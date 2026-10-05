from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.keyboards.shop import products

router=Router()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🏀 BASKETBALL CHALLENGE\n\n"
        "Добро пожаловать в магазин!\n\n"
        "Выберите версию игры:",
        reply_markup=products())
