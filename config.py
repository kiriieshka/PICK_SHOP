import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

# Comma-separated Telegram IDs of users allowed to open /admin.
# Example: ADMIN_IDS=123456789,987654321
ADMIN_IDS = {
    int(value.strip())
    for value in os.getenv("ADMIN_IDS", "").split(",")
    if value.strip().isdigit()
}

# Backward compatibility with the previous single-admin variable.
_old_admin_id = os.getenv("ADMIN_ID", "")
if _old_admin_id.strip().isdigit():
    ADMIN_IDS.add(int(_old_admin_id.strip()))

RETURN_URL = os.getenv("RETURN_URL", "https://t.me/")

DB_ENABLED = os.getenv("DB_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
DATABASE_URL = os.getenv("DATABASE_URL", "")
