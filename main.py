import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from config import TOKEN
from database import init_db

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def main():
    # Удаляем старый webhook (если был), иначе polling не получит обновления
    await bot.delete_webhook(drop_pending_updates=True)
    # Инициализируем базу данных (создаст таблицу, если её нет)
    await init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())