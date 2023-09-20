from aiogram import Router, F
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from bot.states.states import ApplicationCreatingStates
from aiogram.fsm.context import FSMContext
from asyncio import sleep as timeout
from bot.config import config
from aiogram.methods.set_my_commands import SetMyCommands
from aiogram.types import BotCommand, BotCommandScopeChat
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.methods.send_message import SendMessage
from aiogram.methods.edit_message_text import EditMessageText
from bot.keyboards.users import take_application, choose_service_type, choose_form_type, open_webapp
from sqlalchemy import insert, select, update
from bot.database.models import Application, Worker, ApplicationWorkerAssociation
from bot.filters.chats import ChatTypeFilter
from bot.filters.worker import WorkerFilter
from bot.filters.phone import PhoneFilter
from sqlalchemy.orm import exc

user_router = Router()    

@user_router.message(Command("start"), ChatTypeFilter(chat_type=["private"]))
async def help(message: Message):
    await message.answer("Для створення посту введість команду:\n `/post`", parse_mode='Markdown')


@user_router.message(Command("post"), ChatTypeFilter(chat_type=["private"]))
async def make_post(message: Message):
    await message.answer("Оберіть спосіб подачі заявки", reply_markup=choose_form_type())

@user_router.callback_query(Text(startswith="site_form"))
async def fill_site_form(callback: CallbackQuery):

    await callback.message.answer('Відкрити форму:', reply_markup=open_webapp())


@user_router.callback_query(Text(startswith="telegram_answers"))
async def fill_answers(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Надавайте кожну відповідь одним повідомленням")
    await timeout(3)
    await callback.message.answer("Оберіть тип послуг:", reply_markup=choose_service_type())
    await state.set_state(ApplicationCreatingStates.service_type)


@user_router.callback_query(ApplicationCreatingStates.service_type)
async def add_problem(callback: CallbackQuery, state: FSMContext):
    await state.update_data(service_type=callback.data)
    await callback.message.answer("Опишіть суть проблеми одним повідомленням:")
    await state.set_state(ApplicationCreatingStates.problem)


@user_router.message(ApplicationCreatingStates.problem, F.text)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(problem=message.text)
    await message.answer("Вкажіть Ваше ім'я:")
    await state.set_state(ApplicationCreatingStates.name)


@user_router.message(ApplicationCreatingStates.name, F.text)
async def add_contacts(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Вкажіть Ваш номер телефону:")
    await state.set_state(ApplicationCreatingStates.contacts)


@user_router.message(ApplicationCreatingStates.contacts, PhoneFilter())
async def add_address(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer("Вкажіть Вашу адресу:")
    await state.set_state(ApplicationCreatingStates.address)


@user_router.message(ApplicationCreatingStates.address, F.text)
async def send_post(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(address=message.text)
    await message.answer("Дякуємо, очікуйте на відповідь від нашого майстра")
    data = await state.get_data()
    await state.clear()

    post_text = f"🔵 Aктивно\n\n" f'{data["problem"]}\n\n' f'Адреса: `{data["address"]}`'

    chat_id = config.plumbing_chat_id if data["service_type"] == 'plumbing' else config.electricity_chat_id

    post = await SendMessage(
        chat_id=chat_id,
        text=post_text,
        reply_markup=take_application(),
        parse_mode="Markdown",
    )
    post_time = message.date.replace(tzinfo=None)

    insert_query = insert(Application).values(
        application_type=data["service_type"],
        name=data["name"],
        phone=data["contacts"],
        problem=data["problem"],
        address=data["address"],
        post_time=post_time,
        message_id=str(post.message_id)
    )

    await session.execute(insert_query)
    await session.commit()


@user_router.callback_query(Text(startswith="send_customer_info"), WorkerFilter(is_block_check=True))
async def show_contacts(callback: CallbackQuery, session: AsyncSession):
    worker_query = select(Worker).where(Worker.user_id == str(callback.from_user.id))
    worker = (await session.execute(worker_query)).scalar_one()
    
    edited_text = callback.message.text.replace("🔵", "✅")
    edited_text = edited_text.replace("Активно", "Виконується")
            
    application_select = select(Application).where(Application.message_id==str(callback.message.message_id))

    application = (await session.execute(application_select)).scalar_one()
    
    existance_query=select(ApplicationWorkerAssociation.status).where(
        (ApplicationWorkerAssociation.worker_id == worker.id) &
        (ApplicationWorkerAssociation.application_id == application.id)
    )
    
    existing_status = (await session.execute(existance_query)).all()

    if len(existing_status)>0:
        association_query = update(ApplicationWorkerAssociation).where(
            (ApplicationWorkerAssociation.worker_id == worker.id) &
            (ApplicationWorkerAssociation.application_id == application.id)
        ).values(status='Up')
        await session.execute(association_query)
        await session.commit()
    else:
        association = ApplicationWorkerAssociation(
            application_id=application.id,
            worker_id=worker.id,
            status="Up",
            comment=""
        )

        session.add(association)
        await session.commit()

    text = f"Ви взяли замовлення №-{application.id}:\n\n{application.problem}\n\nЗамовник: {application.name}\nКонтакти: `{application.phone}`\nАдреса: `{application.address}`"

    await SendMessage(chat_id=callback.from_user.id, text=text, parse_mode='Markdown')

    await EditMessageText(
        chat_id=callback.message.chat.id,
        text=edited_text,
        message_id=callback.message.message_id,
        reply_markup=None,
        parse_mode="Markdown",
    )

@user_router.callback_query(Text(startswith="send_customer_info"), ~WorkerFilter())
async def show_contacts(callback: CallbackQuery, session: AsyncSession):
    text=f'{callback.from_user.first_name}, Ви не є виконавцем. Щоб зареєструватись використайте команду:\n`/registration` в [бесіді]({config.invite_link}) з ботом'
    await callback.message.answer(text=text, parse_mode='Markdown')
    registration_commands = [
        BotCommand(command="registration", description="Зареєструватись як робітник")
    ]
    await SetMyCommands(commands=registration_commands, scope=BotCommandScopeChat(chat_id=callback.from_user.id))
    
    