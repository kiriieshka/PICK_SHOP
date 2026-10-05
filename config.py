import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
RETURN_URL = os.getenv("RETURN_URL", "https://t.me/")

DB_ENABLED = os.getenv("DB_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
DATABASE_URL = os.getenv("DATABASE_URL", "")
