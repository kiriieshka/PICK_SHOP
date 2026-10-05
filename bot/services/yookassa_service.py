import uuid

from yookassa import Configuration, Payment

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, RETURN_URL


def validate_config():
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise RuntimeError(
            "YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY are not set"
        )

    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY


def create_payment(amount_rub, description, order_id):
    validate_config()

    return Payment.create(
        {
            "amount": {
                "value": f"{amount_rub:.2f}",
                "currency": "RUB",
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": RETURN_URL,
            },
            "description": description,
            "metadata": {
                "order_id": str(order_id),
            },
        },
        uuid.uuid4().hex,
    )


def get_payment(payment_id):
    validate_config()
    return Payment.find_one(payment_id)
