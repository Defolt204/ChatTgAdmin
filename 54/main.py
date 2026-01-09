import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import config
from database.manager import init_db
from handlers import admin, user, warns, settings, common, security, social, events
from middlewares.role_check import RoleMiddleware
from middlewares.stats_tracker import StatsMiddleware
from middlewares.filter import FilterMiddleware

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize database
    await init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares
    dp.message.outer_middleware(RoleMiddleware())
    dp.callback_query.outer_middleware(RoleMiddleware())
    dp.message.outer_middleware(StatsMiddleware())
    dp.message.outer_middleware(FilterMiddleware())

    # Register Routers
    dp.include_router(admin.router)
    dp.include_router(settings.router)
    dp.include_router(security.router)
    dp.include_router(social.router)
    dp.include_router(events.router)
    dp.include_router(warns.router)
    dp.include_router(user.router)
    dp.include_router(common.router)
    # Logic in common.py: @router.message(F.text == "!help") ... @router.message(F.text.startswith("!")) -> unknown
    # So common.router MUST be LAST.
    
    # Remove common from top?
    # In original file it was last:
    # dp.include_router(admin.router)
    # ...
    # dp.include_router(common.router)
    
    # So I will re-add it at the end.
    
    # Current list in file:
    # dp.include_router(admin.router)
    # dp.include_router(user.router)
    # dp.include_router(warns.router)
    # dp.include_router(settings.router)
    # dp.include_router(common.router)
    
    # I will replace the whole block.


    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
