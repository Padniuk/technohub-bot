from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def take_application():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Взяти замовлення', 
        callback_data='send_customer_info')
    )
    return keyboard.as_markup()