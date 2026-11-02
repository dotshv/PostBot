import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from database import init_db, close_db
from handlers import (
    start,
    create_post,
    buttons,
    inline_query,
    my_posts,
    channel_post,
    broadcast,
    donate,
    profile,
    language,
    help
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PostBot")

async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN is not configured in .env")
        sys.exit(1)

    await init_db()

    session = AiohttpSession()
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    try:
        me = await bot.get_me()
        if not config.BOT_USERNAME or config.BOT_USERNAME == "YOUR_BOT_USERNAME":
            config.BOT_USERNAME = me.username
        logger.info(f"PostBot online as @{me.username}")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return

    await bot.set_my_commands([
        BotCommand(command="start", description="Open main menu"),
        BotCommand(command="new", description="Create new post"),
        BotCommand(command="cast", description="Broadcast message (Admin)"),
        BotCommand(command="donate", description="Support PostBot"),
        BotCommand(command="lang", description="Change language"),
    ])

    dp.include_router(start.router)
    dp.include_router(donate.router)
    dp.include_router(buttons.router)
    dp.include_router(create_post.router)
    dp.include_router(channel_post.router)
    dp.include_router(broadcast.router)
    dp.include_router(inline_query.router)
    dp.include_router(my_posts.router)
    dp.include_router(profile.router)
    dp.include_router(language.router)
    dp.include_router(help.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
