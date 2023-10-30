from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import Worker


class WorkerFilter(BaseFilter):
    def __init__(self, is_block_check=False):
        self.is_block_check = is_block_check

    async def __call__(self, message: Message, session: AsyncSession):
        worker_query = select(Worker).where(Worker.user_id == str(message.from_user.id))
        worker = (await session.execute(worker_query)).scalar()
        if self.is_block_check and worker:
            return not worker.blocked
        else:
            return True if worker else False
