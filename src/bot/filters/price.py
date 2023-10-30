from aiogram.filters import BaseFilter
from aiogram.types import Message


class PriceFilter(BaseFilter):
    async def __call__(self, message: Message):
        price = message.text
        if price.isdigit():
            return True
        else:
            text = "Сума має бути вказана числом"
            await message.answer(text, parse_mode="Markdown")
            return False
