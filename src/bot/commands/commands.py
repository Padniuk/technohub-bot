from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from bot.config import config

async def set_commands(bot: Bot):
    await user_commands(bot)
    await admin_commands(bot)


async def user_commands(bot: Bot):
    user_commands = [
        BotCommand(command="start", description="Start of the bot"),
        BotCommand(command="post", description="Create a post")
    ]
    
    await bot.set_my_commands(
        user_commands, 
        scope=BotCommandScopeAllPrivateChats()
    )

async def admin_commands(bot: Bot):
    admin_commands = [
        BotCommand(command="worker_status", description="Incividual worker statistics"),
        BotCommand(command="plumbing_day_report", description="Plumbing statistics"),
        BotCommand(command="electricity_day_report", description="Electricity statistics"),
        BotCommand(command="free_applications", description="Info about free applications")
    ]
    for admin_id in config.admins_id.split(', '):
        await bot.set_my_commands(
            admin_commands, 
            scope=BotCommandScopeChat(chat_id=admin_id)
        )