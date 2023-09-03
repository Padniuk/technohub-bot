import asyncio
from aiogram import Bot, Dispatcher
from config import config
from commands import set_commands
from handlers import user_router, worker_router, admin_router
from aiogram.fsm.storage.memory import MemoryStorage
from middlewares import DbSessionMiddleware
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import logging

async def main():
    if config.debug:
        logging.basicConfig(level=logging.DEBUG)

    db_url = URL.create(
        drivername='postgresql+asyncpg',
        database=config.db_name,
        host=config.db_host,
        username=config.db_user,
        password=config.db_pass
    )

    engine = create_async_engine(url=db_url, echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.bot_token.get_secret_value())
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))

    dp.include_routers(user_router, worker_router, admin_router)
    
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())