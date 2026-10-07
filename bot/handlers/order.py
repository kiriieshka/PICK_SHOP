from aiogram import Router,F
from aiogram.types import CallbackQuery,Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Bot
from config import ADMIN_IDS,BOT_TOKEN
from bot.states.order_states import OrderStates
from bot.database.db import get_latest_paid_paper_order,get_order,set_order_details
from bot.keyboards.shop import products

router=Router()

@router.callback_query(F.data=="check_payment")
async def check_payment(c: CallbackQuery):
    await c.answer("После успешной оплаты ЮKassa автоматически пришлет подтверждение.",show_alert=True)

@router.message(Command("delivery"))
async def delivery(message:Message,state:FSMContext):
    paid=await get_latest_paid_paper_order(message.from_user.id)
    if not paid:
        await message.answer("Оплаченный заказ на бумажную версию не найден.")
        return
    await state.update_data(paper_order_id=paid["id"])
    await state.set_state(OrderStates.waiting_full_name)
    await message.answer("👤 Введите ФИО получателя:")

@router.message(OrderStates.waiting_full_name)
async def full_name(message:Message,state:FSMContext):
    value=(message.text or "").strip()
    if len(value)<5 or len(value)>255:
        await message.answer("Введите корректное ФИО.")
        return
    await state.update_data(full_name=value)
    await state.set_state(OrderStates.waiting_address)
    await message.answer("📍 Теперь введите полный адрес получателя:")

@router.message(OrderStates.waiting_address)
async def address(message:Message,state:FSMContext):
    value=(message.text or "").strip()
    if len(value)<10 or len(value)>2000:
        await message.answer("Введите полный адрес получателя.")
        return
    data=await state.get_data()
    order_id=data.get("paper_order_id")
    order=await get_order(order_id) if order_id else None
    if not order or order["telegram_id"]!=message.from_user.id:
        await state.clear()
        await message.answer("Заказ не найден.",reply_markup=products())
        return
    await set_order_details(order_id,data["full_name"],value)
    await state.clear()
    await message.answer(f"✅ Заказ #{order_id} оформлен!\n\n📦 Бумажная версия\nДанные для доставки получены.",reply_markup=products())
    if ADMIN_ID:
        bot=Bot(BOT_TOKEN)
        try:
            await bot.send_message(ADMIN_ID,
                f"📦 НОВЫЙ ЗАКАЗ #{order_id}\n\nТовар: БУМАЖНАЯ ВЕРСИЯ\n"
                f"Сумма: {order['amount']} ₽\nСтатус: ОПЛАЧЕНО\n\n"
                f"👤 ФИО:\n{data['full_name']}\n\n📍 Адрес:\n{value}\n\n"
                f"🆔 Telegram ID: {message.from_user.id}\n@{message.from_user.username or 'нет'}\n"
                f"Payment ID: {order['payment_id']}")
        finally:
            await bot.session.close()
