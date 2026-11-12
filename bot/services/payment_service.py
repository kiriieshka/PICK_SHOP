from aiogram import Bot

from config import BOT_TOKEN, ADMIN_IDS
from bot.database.db import (
    get_order_by_payment,
    mark_paid,
    issue_key,
)
from bot.services.yookassa_service import get_payment


async def process_yookassa_event(payload):
    if payload.get("event") != "payment.succeeded":
        return

    obj = payload.get("object") or {}
    payment_id = obj.get("id")

    if not payment_id:
        return

    # Проверяем платёж непосредственно через YooKassa
    payment = get_payment(payment_id)

    if payment.status != "succeeded" or payment.paid is not True:
        return

    order = await get_order_by_payment(payment_id)

    if not order:
        return

    # Защита от повторной обработки webhook
    if order["status"] in ("paid", "details_received"):
        return

    # Проверяем сумму платежа
    paid_value = float(payment.amount.value)
    order_value = float(order["amount"])

    if abs(paid_value - order_value) > 0.001:
        raise RuntimeError(
            f"Payment amount mismatch for order #{order['id']}"
        )

    await mark_paid(order["id"])

    bot = Bot(BOT_TOKEN)

    try:
        if order["product"] == "electronic":
            code = await issue_key(
                order["id"],
                order["telegram_id"],
            )

            # Сообщение покупателю
            await bot.send_message(
                order["telegram_id"],
                "✅ Оплата прошла успешно!\n\n"
                "💻 Электронная версия оплачена.\n\n"
                f"🔑 Ваш ключ доступа:\n<code>{code}</code>\n\n"
                "Откройте игровой бот, отправьте /start "
                "и введите этот 10-значный код.",
                parse_mode="HTML",
            )

            # Уведомление администраторам
            if ADMIN_IDS:
                for admin_id in ADMIN_IDS:
                    await bot.send_message(
                        admin_id,
                        "💻 ПРОДАЖА ЭЛЕКТРОННОЙ ВЕРСИИ\n\n"
                        f"Заказ #{order['id']}\n"
                        f"Сумма: {order['amount']} ₽\n"
                        f"Telegram ID: {order['telegram_id']}\n"
                        f"Payment ID: {payment_id}\n"
                        f"Ключ: <code>{code}</code>",
                        parse_mode="HTML",
                    )

        elif order["product"] == "paper":
            # Сообщение покупателю
            await bot.send_message(
                order["telegram_id"],
                f"✅ Оплата заказа #{order['id']} "
                f"на {order['amount']} ₽ прошла успешно!\n\n"
                "📦 Бумажная версия.\n\n"
                "Чтобы оформить доставку, отправьте /delivery.",
            )

            # Уведомление администраторам
            if ADMIN_IDS:
                for admin_id in ADMIN_IDS:
                    await bot.send_message(
                        admin_id,
                        f"💳 ОПЛАЧЕН ЗАКАЗ #{order['id']}\n\n"
                        f"📦 Бумажная версия — {order['amount']} ₽\n"
                        f"Telegram ID: {order['telegram_id']}\n"
                        f"Payment ID: {payment_id}\n\n"
                        "Ожидаются ФИО и адрес.",
                    )

    finally:
        await bot.session.close()