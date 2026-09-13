import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, OWNER_ID, DB_PATH, LOG_LEVEL
from database.models import init_db
from database.queries import DB
from utils.logger import setup_logging
from handlers.owner import router as owner_router
from handlers.admin import router as admin_router
from handlers.join_requests import router as join_router
from handlers.users import router as users_router

async def main():
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN missing in .env")
    if not OWNER_ID: raise RuntimeError("OWNER_ID missing in .env")
    setup_logging(LOG_LEVEL)
    await init_db(DB_PATH)
    db=DB(DB_PATH)
    bot=Bot(BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp=Dispatcher(storage=MemoryStorage())

    # Dependency injection for handlers.
    dp["db"]=db

    # Specific routers first, catch-all tracker last.
    dp.include_router(owner_router)
    dp.include_router(admin_router)
    dp.include_router(join_router)
    dp.include_router(users_router)

    me=await bot.get_me()
    logging.info("Started @%s (%s)",me.username,me.id)
    try:
        await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__=="__main__":
    asyncio.run(main())
