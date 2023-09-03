from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def show_applications(applications: list):
    keyboard = InlineKeyboardBuilder()
    for application in applications:
        keyboard.row(InlineKeyboardButton(
            text=application[0], 
            callback_data=f'chose_application_{application[1]}')
        )
    return keyboard.as_markup()