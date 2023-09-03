from aiogram import Router, F
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from states import ApplicationCreatingStates
from aiogram.fsm.context import FSMContext
from asyncio import sleep as timeout
from config import config
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.methods.send_message import SendMessage
from aiogram.methods.edit_message_text import EditMessageText
from keyboards import take_application
from sqlalchemy import insert, select
from database import Application, Worker, ApplicationWorkerAssociation
from filters import ChatTypeFilter, PhoneFilter
from sqlalchemy.orm import exc
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.web_app_info import WebAppInfo
from config import config

router = Router()

@router.message(Command("site_post"))
async def site_post(message: Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text='Взяти замовлення', 
        web_app=WebAppInfo(url=config.plumbing_url))
    )
    await message.answer('Відкрити сайт', reply_markup=keyboard.as_markup())

@router.message(Command("start"), ChatTypeFilter(chat_type=["private"]))
async def help(message: Message):
    await message.answer("Для створення посту введість команду:\n `/post`", parse_mode='Markdown')


@router.message(Command("post"), ChatTypeFilter(chat_type=["private"]))
async def make_post(message: Message, state: FSMContext):
    await message.answer("Надавайте кожну відповідь одним повідомленням")
    await timeout(1)
    await message.answer("Опишіть суть проблеми одним повідомленням:")
    await state.set_state(ApplicationCreatingStates.problem)


@router.message(ApplicationCreatingStates.problem, F.text)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(problem=message.text)
    await message.answer("Вкажіть Ваше ім'я:")
    await state.set_state(ApplicationCreatingStates.name)


@router.message(ApplicationCreatingStates.name, F.text)
async def add_contacts(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Вкажіть Ваш номер телефону:")
    await state.set_state(ApplicationCreatingStates.contacts)


@router.message(ApplicationCreatingStates.contacts, PhoneFilter())
async def add_address(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer("Вкажіть Вашу адресу:")
    await state.set_state(ApplicationCreatingStates.address)


@router.message(ApplicationCreatingStates.address, F.text)
async def send_post(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(address=message.text)
    await message.answer("Дякуємо, очікуйте на відповідь від нашого майстра")
    data = await state.get_data()
    await state.clear()

    post_text = f"🔵 Aктивно\n\n" f'{data["problem"]}\n\n' f'Адреса: `{data["address"]}`'

    post = await SendMessage(
        chat_id=config.electricity_chat_id,
        text=post_text,
        reply_markup=take_application(),
        parse_mode="Markdown",
    )
    post_time = message.date.replace(tzinfo=None)

    insert_query = insert(Application).values(
        application_type='electricity',
        name=data["name"],
        phone=data["contacts"],
        problem=data["problem"],
        address=data["address"],
        post_time=post_time,
        message_id=str(post.message_id)
    )

    await session.execute(insert_query)
    await session.commit()


@router.callback_query(Text(startswith="send_customer_info"))
async def show_contacts(callback: CallbackQuery, session: AsyncSession):
    try:
        worker_query = select(Worker).where(Worker.user_id == str(callback.from_user.id))
        worker = (await session.execute(worker_query)).scalar_one()
        
        edited_text = callback.message.text.replace("🔵", "✅")
        edited_text = edited_text.replace("Активно", "Виконується")
        
        await EditMessageText(
            chat_id=callback.message.chat.id,
            text=edited_text,
            message_id=callback.message.message_id,
            reply_markup=None,
            parse_mode="Markdown",
        )


        address = edited_text.split("\n")[-1].split(": ")[-1]
        problem = edited_text.split("\n")[2]
        

        application_select = select(Application).where(
            (Application.address == address) &
            (Application.problem == problem)
        )

        application = (await session.execute(application_select)).scalar_one()

        association = ApplicationWorkerAssociation(
            application_id=application.id,
            worker_id=worker.id,
            status="Up",
            comment=""
        )

        session.add(association)
        await session.commit()

        text = f"Ви взяли замовлення:\n\n{application.problem}\n\nЗамовник: {application.name}\nКонтакти: `{application.phone}`\nАдреса: `{application.address}`"

        await SendMessage(chat_id=callback.from_user.id, text=text, parse_mode='Markdown')

    except exc.NoResultFound:
        await callback.message.answer('Ви не є виконавцем, щоб зареєструватись використайте команду:\n`/registration`', parse_mode='Markdown')
    
