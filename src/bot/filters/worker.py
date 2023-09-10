from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Worker

class WorkerFilter(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession):
        worker_query = select(Worker).where(Worker.user_id==str(message.from_user.id))
        return True if (await session.execute(worker_query)).first() else False