from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from config import config

async def set_commands(bot: Bot):
    await user_commands(bot)
    await admin_commands(bot)
    await group_commands(bot)


async def user_commands(bot: Bot):
    user_commands = [
        BotCommand(command="start", description="Start of the bot"),
        BotCommand(command="post", description="Create a post")
    ]
    
    await bot.set_my_commands(
        user_commands, 
        scope=BotCommandScopeAllPrivateChats()
    )


async def group_commands(bot: Bot):
    group_commands = [
        BotCommand(command="registration", description="Registrate as worker")
    ]
    
    await bot.set_my_commands(
        group_commands, 
        scope=BotCommandScopeChat(chat_id=config.electricity_chat_id)
    )
    await bot.set_my_commands(
        group_commands, 
        scope=BotCommandScopeChat(chat_id=config.plumbing_chat_id)
    )


async def admin_commands(bot: Bot):
    admin_commands = [
        BotCommand(command="worker_status", description="Incividual worker statistics"),
        BotCommand(command="day_report", description="All worker statistics")
    ]
    
    await bot.set_my_commands(
        admin_commands, 
        scope=BotCommandScopeChat(chat_id=config.admins_id)
    )