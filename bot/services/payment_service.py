from aiogram import Bot

from config import BOT_TOKEN, ADMIN_ID
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

    # The webhook body is treated as a trigger only.
    # We ask YooKassa for the payment itself before delivering anything.
    payment = get_payment(payment_id)

    if payment.status != "succeeded" or payment.paid is not True:
        return

    order = await get_order_by_payment(payment_id)

    if not order:
        return

    # Idempotency: YooKassa may retry the same webhook.
    if order["status"] in ("paid", "details_received"):
        return

    # Make sure the payment is for the amount recorded in our order.
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

            await bot.send_message(
                order["telegram_id"],
                "✅ Оплата прошла успешно!\n\n"
                "💻 Электронная версия оплачена.\n\n"
                f"🔑 Ваш ключ доступа:\n<code>{code}</code>\n\n"
                "Откройте игровой бот, отправьте /start "
                "и введите этот 10-значный код.",
                parse_mode="HTML",
            )

            if ADMIN_ID:
                await bot.send_message(
                    ADMIN_ID,
                    "💻 ПРОДАЖА ЭЛЕКТРОННОЙ ВЕРСИИ\n\n"
                    f"Заказ #{order['id']}\n"
                    f"Сумма: {order['amount']} ₽\n"
                    f"Telegram ID: {order['telegram_id']}\n"
                    f"Payment ID: {payment_id}\n"
                    f"Ключ: <code>{code}</code>",
                    parse_mode="HTML",
                )

        elif order["product"] == "paper":
            await bot.send_message(
                order["telegram_id"],
                f"✅ Оплата заказа #{order['id']} "
                f"на {order['amount']} ₽ прошла успешно!\n\n"
                "📦 Бумажная версия.\n\n"
                "Чтобы оформить доставку, отправьте /delivery.",
            )

            if ADMIN_ID:
                await bot.send_message(
                    ADMIN_ID,
                    f"💳 ОПЛАЧЕН ЗАКАЗ #{order['id']}\n\n"
                    f"📦 Бумажная версия — {order['amount']} ₽\n"
                    f"Telegram ID: {order['telegram_id']}\n"
                    f"Payment ID: {payment_id}\n\n"
                    "Ожидаются ФИО и адрес.",
                )

    finally:
        await bot.session.close()
