import asyncio
import os
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from database import init_db

load_dotenv()

# Приоритет: зашифрованный токен > обычный .env
MASTER_KEY = os.getenv("MASTER_KEY")
if MASTER_KEY:
    from security import decrypt_token
    TOKEN = decrypt_token(MASTER_KEY)
    print("Токен загружен из зашифрованного файла (AES-128)")
else:
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Токен не найден! Установи MASTER_KEY или BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def health_check(request):
    return web.Response(text="OK")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await init_db()

    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Бот запущен! Веб-сервер на порту {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())