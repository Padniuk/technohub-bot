from aiogram.filters import BaseFilter
from aiogram.types import Message


class PhoneFilter(BaseFilter):
    async def __call__(self, message: Message):
        phone = message.text
        if phone[0]=='+' and phone[1:].isdigit() and len(phone) == 12:
            return True
        elif phone.isdigit() and len(phone) == 12:
            return True
        elif phone.isdigit() and len(phone) == 10:
            return True
        else:
            text = "Введіть телефон в одному з заданих форматів:\n`+380686667788`\nабо `380686667788`\nабо `0686667788`"
            await message.answer(text, parse_mode="Markdown")
            return False
