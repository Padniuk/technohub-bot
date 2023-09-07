from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def show_workers(workers: list):
    keyboard = InlineKeyboardBuilder()
    for worker in workers:
        service = 'Сантехнік' if worker[2] == 'plumbing' else 'Електрик'
        keyboard.row(InlineKeyboardButton(
            text=f'{service}: {worker[0]}', 
            callback_data=f'worker_{worker[0]}_{worker[1]}')
        )
    return keyboard.as_markup()