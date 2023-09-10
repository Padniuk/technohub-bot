from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.config import config

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message):
        return str(message.from_user.id) in config.admins_id.split(', ')