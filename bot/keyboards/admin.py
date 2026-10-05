from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
         InlineKeyboardButton(text="📦 Заказы", callback_data="admin:orders")],
        [InlineKeyboardButton(text="🔑 Ключи", callback_data="admin:keys"),
         InlineKeyboardButton(text="➕ Создать ключи", callback_data="admin:generate")],
    ])

def admin_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Админ-панель", callback_data="admin:menu")]
    ])
