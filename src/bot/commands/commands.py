from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from bot.config import config

async def set_commands(bot: Bot):
    await user_commands(bot)
    await work_chat_commands(bot)
    await admin_commands(bot)


async def user_commands(bot: Bot):
    user_commands = [
        BotCommand(command="start", description="Чим я можу допомогти"),
        BotCommand(command="post", description="Створити пост")
    ]
    
    await bot.set_my_commands(
        user_commands, 
        scope=BotCommandScopeAllPrivateChats()
    )

async def work_chat_commands(bot: Bot):
    work_chat_commands = []
    await bot.set_my_commands(
        work_chat_commands,
        scope=BotCommandScopeChat(chat_id=config.electricity_chat_id)
    )
    await bot.set_my_commands(
        work_chat_commands,
        scope=BotCommandScopeChat(chat_id=config.plumbing_chat_id)
    )

async def admin_commands(bot: Bot):
    admin_commands = [
        BotCommand(command="worker_status", description="Індивідуальна статистика"),
        BotCommand(command="plumbing_day_report", description="Статистика сантехніків"),
        BotCommand(command="electricity_day_report", description="Статистика електриків"),
        BotCommand(command="free_applications", description="Активні та скасовані заявки")
    ]
    for admin_id in config.admins_id.split(', '):
        await bot.set_my_commands(
            admin_commands, 
            scope=BotCommandScopeChat(chat_id=admin_id)
        )