from aiogram import Router,F
from aiogram.types import CallbackQuery
from bot.keyboards.shop import products,pay_button
from bot.database.db import create_order,set_payment_id
from bot.services.yookassa_service import create_payment

router=Router()

@router.callback_query(F.data=="shop:back")
async def shop_back(c: CallbackQuery):
    await c.message.edit_text("🛒 Выберите версию игры:",reply_markup=products())
    await c.answer()

@router.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    product=c.data.split(":",1)[1]
    if product=="electronic":
        amount,title=500,"Электронная версия BASKETBALL CHALLENGE"
    elif product=="paper":
        amount,title=1000,"Бумажная версия BASKETBALL CHALLENGE"
    else:
        await c.answer("Неизвестный товар.",show_alert=True)
        return
    order_id=await create_order(c.from_user.id,c.from_user.username,product,amount)
    payment=create_payment(amount,f"{title}, заказ #{order_id}",order_id)
    await set_payment_id(order_id,payment.id)
    await c.message.edit_text(
        f"🧾 ЗАКАЗ #{order_id}\n\n{title}\n💰 {amount} ₽\n\nНажмите кнопку ниже для оплаты.",
        reply_markup=pay_button(payment.confirmation.confirmation_url))
    await c.answer()
