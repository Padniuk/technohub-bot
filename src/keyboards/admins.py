from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def show_workers(workers: list):
    keyboard = InlineKeyboardBuilder()
    for worker in workers:
        keyboard.row(InlineKeyboardButton(
            text=worker[0], 
            callback_data=f'worker_{worker[0]}_{worker[1]}')
        )
    return keyboard.as_markup()