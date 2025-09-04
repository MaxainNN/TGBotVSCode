import asyncio
import logging
from aiogram import Bot, Dispatcher

import app.config as cfg
import app.db as db
from app.handlers import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=cfg.API_TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router=router)
    await db.create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())