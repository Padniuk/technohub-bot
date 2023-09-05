from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.web_app_info import WebAppInfo
from bot.config import config

def take_application():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Взяти замовлення', 
        callback_data='send_customer_info')
    )
    return keyboard.as_markup()

def choose_service_type():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Сантехніка', 
        callback_data='plumbing')
    )
    keyboard.row(InlineKeyboardButton(
        text='Електрика', 
        callback_data='electricity')
    )
    return keyboard.as_markup()

def choose_form_type():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Телеграм опитування', 
        callback_data='telegram_answers')
    )
    keyboard.row(InlineKeyboardButton(
        text='Заповнити форму', 
        callback_data='site_form')
    )
    return keyboard.as_markup()

def open_webapp():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Зробити замовлення', 
        web_app=WebAppInfo(url=config.plumbing_url))
    )
    return keyboard.as_markup()