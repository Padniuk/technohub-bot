from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.types.chat_member_member import ChatMemberStatus
from aiogram.methods.get_chat_member import GetChatMember
from bot.config import config

class RegistrationFilter(BaseFilter):
    async def __call__(self, message: Message):
        plumbing_chat_member = await GetChatMember(chat_id=config.plumbing_chat_id, user_id=message.from_user.id)
        electricity_chat_member = await GetChatMember(chat_id=config.electricity_chat_id, user_id=message.from_user.id)
        return plumbing_chat_member.status == ChatMemberStatus.MEMBER or electricity_chat_member.status == ChatMemberStatus.MEMBER# or \
            # plumbing_chat_member.status == ChatMemberStatus.ADMINISTRATOR or electricity_chat_member.status == ChatMemberStatus.ADMINISTRATOR or \
            # plumbing_chat_member.status == ChatMemberStatus.CREATOR or electricity_chat_member.status == ChatMemberStatus.CREATOR
