import asyncio
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
import uvicorn

from config import BOT_TOKEN
from bot.database.db import init_db, close_db
from bot.handlers import start, shop, order, admin
from bot.services.yookassa_service import validate_config

app = FastAPI(title="Basketball Shop Bot")

@app.get("/")
async def root():
    return {"ok": True}

@app.post("/yookassa/webhook")
async def yookassa_webhook(payload: dict):
    from bot.services.payment_service import process_yookassa_event
    await process_yookassa_event(payload)
    return {"ok": True}

async def run_http():
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=8000))
    await server.serve()

async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    # validate_config()
    await init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_routers(start.router, shop.router, order.router, admin.router)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()

async def main():
    await asyncio.gather(run_bot(), run_http())

if __name__ == "__main__":
    asyncio.run(main())
