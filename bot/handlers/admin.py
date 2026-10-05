from aiogram import Router,F
from aiogram.filters import Command
from aiogram.types import Message,CallbackQuery
from config import ADMIN_ID
from bot.keyboards.admin import admin_menu,admin_back
from bot.database.db import get_orders,get_sales_stats,get_key_stats,generate_keys

router=Router()
def is_admin(uid): return bool(ADMIN_ID and uid==ADMIN_ID)

@router.message(Command("admin"))
async def admin(message:Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа."); return
    await message.answer("👨‍💼 АДМИН-ПАНЕЛЬ",reply_markup=admin_menu())

@router.callback_query(F.data=="admin:menu")
async def menu(c:CallbackQuery):
    if not is_admin(c.from_user.id): await c.answer("Нет доступа.",show_alert=True); return
    await c.message.edit_text("👨‍💼 АДМИН-ПАНЕЛЬ",reply_markup=admin_menu()); await c.answer()

@router.callback_query(F.data=="admin:stats")
async def stats(c:CallbackQuery):
    if not is_admin(c.from_user.id): await c.answer("Нет доступа.",show_alert=True); return
    count,total=await get_sales_stats()
    await c.message.edit_text(f"📊 СТАТИСТИКА\n\nОплаченных заказов: {count}\nВыручка: {total:.2f} ₽",reply_markup=admin_back()); await c.answer()

@router.callback_query(F.data=="admin:orders")
async def orders(c:CallbackQuery):
    if not is_admin(c.from_user.id): await c.answer("Нет доступа.",show_alert=True); return
    rows=await get_orders(20)
    text="📦 ПОСЛЕДНИЕ ЗАКАЗЫ\n\n"+("\n\n".join(
        f"#{o['id']} — {o['product']} — {o['amount']} ₽\nСтатус: {o['status']}\nTG: {o['telegram_id']}" for o in rows
    ) if rows else "Заказов пока нет.")
    await c.message.edit_text(text,reply_markup=admin_back()); await c.answer()

@router.callback_query(F.data=="admin:keys")
async def keys(c:CallbackQuery):
    if not is_admin(c.from_user.id): await c.answer("Нет доступа.",show_alert=True); return
    s=await get_key_stats()
    await c.message.edit_text(f"🔑 КЛЮЧИ\n\nСвободно: {s.get('available',0)}\nВыдано: {s.get('issued',0)}\nАктивировано: {s.get('activated',0)}",reply_markup=admin_back()); await c.answer()

@router.callback_query(F.data=="admin:generate")
async def generate(c:CallbackQuery):
    if not is_admin(c.from_user.id): await c.answer("Нет доступа.",show_alert=True); return
    codes=await generate_keys(10)
    await c.message.edit_text("✅ Создано 10 ключей.\n\n"+"\n".join(f"<code>{x}</code>" for x in codes),parse_mode="HTML",reply_markup=admin_back()); await c.answer()
