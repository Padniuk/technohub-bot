from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def show_workers(workers: list, lock=False):
    keyboard = InlineKeyboardBuilder()
    for worker in workers:
        service = "Сантехнік" if worker[2] == "plumbing" else "Електрик"
        keyboard.row(
            InlineKeyboardButton(
                text=f"{service}: {worker[0]}",
                callback_data=f"worker_{worker[0]}_{worker[1]}_{worker[3]}"
                if not lock
                else f"blocked-worker_{worker[0]}_{worker[1]}",
            )
        )
    return keyboard.as_markup()


def make_report_navigation(application_type, application_status, offset=0):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="<", callback_data=f"report_{application_type}_left_{offset+1}_{application_status}"
        ),
        InlineKeyboardButton(text="Закрити", callback_data="remove_message"),
        InlineKeyboardButton(
            text=">", callback_data=f"report_{application_type}_right_{offset-1}_{application_status}"
        ),
    )
    return keyboard.as_markup()

def make_worker_data_navigation(worker_id, offset=0):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="<", callback_data=f"worker_data_{worker_id}_{offset+1}"
        ),
        InlineKeyboardButton(text="Закрити", callback_data="remove_message"),
        InlineKeyboardButton(
            text=">", callback_data=f"worker_data_{worker_id}_{offset-1}"
        ),
    )
    return keyboard.as_markup()

def make_categories(application_type):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="✔️ Виконані", callback_data=f"category_Ready_{application_type}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="⚙️ В роботі", callback_data=f"category_Up_{application_type}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="❌ Скасовані", callback_data=f"category_Canceled_{application_type}"
        )
    )
    return keyboard.as_markup()

def make_free_application_navigation(offset=0):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="<", callback_data=f"free_app_{offset+1}"
        ),
        InlineKeyboardButton(text="Закрити", callback_data="remove_message"),
        InlineKeyboardButton(
            text=">", callback_data=f"free_app_{offset-1}"
        ),
    )
    return keyboard.as_markup()

def close_free_applications():
    keyboard=InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="Закрити",
            callback_data="remove_message"
        )
    )
    return keyboard.as_markup()

def make_application_list(applications: list):
    keyboard=InlineKeyboardBuilder()
    for application in applications:
        keyboard.row(
            InlineKeyboardButton(
                text=f"Адреса: {application['address']}",
                callback_data=f"close_application_{application['id']}_{application['application_type']}"
            )
        )
    
    return keyboard.as_markup()