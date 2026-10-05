from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def products():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Электронная версия — 500 ₽", callback_data="buy:electronic")],
        [InlineKeyboardButton(text="📦 Бумажная версия — 1000 ₽", callback_data="buy:paper")],
    ])

def pay_button(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton(text="◀️ К товарам", callback_data="shop:back")],
    ])
