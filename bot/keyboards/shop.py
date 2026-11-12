from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def products():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Электронная версия — 1000 ₽", callback_data="buy:electronic")],
        [InlineKeyboardButton(text="📦 Бумажная версия + Шуткоуч в подарок — 2500 ₽", url="https://www.wildberries.ru/catalog/2238508504/detail.aspx?targetUrl=SN")],
    ])

def pay_button(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton(text="◀️ К товарам", callback_data="shop:back")],
    ])
