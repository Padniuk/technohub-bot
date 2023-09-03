from aiogram import Router, F
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery, Chat
from aiogram.fsm.context import FSMContext
from database import Worker, Application, ApplicationWorkerAssociation
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.methods.set_my_commands import SetMyCommands
from aiogram.types import BotCommand, BotCommandScopeChat
from states import WorkerStates, CancelStates, CompleteStates
from aiogram.methods.send_message import SendMessage
from aiogram.methods.edit_message_text import EditMessageText
from sqlalchemy import insert, select, update, and_
from filters import ChatTypeFilter, PhoneFilter
from aiogram.methods import GetFile
from config import config
from keyboards import show_applications, take_application
import datetime

router = Router()


@router.message(Command("registration"))
async def add_worker(message: Message, state: FSMContext):
    await message.answer("Введіть ім'я:")
    await state.set_state(WorkerStates.name)


@router.message(WorkerStates.name, F.text)
async def add_worker_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введіть телефон:")
    await state.set_state(WorkerStates.phone)


@router.message(WorkerStates.phone, PhoneFilter())    
async def save_data(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    await state.clear()
    user_id = message.from_user.id

    worker_query = insert(Worker).values(
        worker_type='electricity',
        name=data["name"],
        user_id=str(user_id),
        phone=data["phone"]
    )

    worker_commands = [
        BotCommand(command="cancel", description="Cancel an application"),
        BotCommand(command="complete", description="Complete an application")
    ]

    await session.execute(worker_query)
    await session.commit()
    
    await SetMyCommands(commands=worker_commands, scope=BotCommandScopeChat(chat_id=user_id))
    await message.answer("Робітник доданий в базу")


@router.message(Command("complete"))
async def show_all_applications(message: Message, state: FSMContext, session: AsyncSession):
    application_query = (
        select(Application)
        .join(ApplicationWorkerAssociation)
        .join(Worker)
        .where(and_(Worker.user_id == str(message.from_user.id), ApplicationWorkerAssociation.status == 'Up'))
    )

    application_request = await session.execute(application_query)
    applications = [(application.address,application.id) for application in application_request.scalars()]
    
    await message.answer("Виберіть замовлення:", reply_markup=show_applications(applications))
    await state.set_state(CompleteStates.application_id)


@router.callback_query(Text(startswith="chose_application"), CompleteStates.application_id)
async def chose_application(callback: CallbackQuery, state: FSMContext): 
    await state.update_data(application_id=int(callback.data.split('_')[2]))
    await callback.message.answer("Вкажіть суму:")
    await state.set_state(CompleteStates.price)


@router.message(CompleteStates.price)
async def get_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    await message.answer("Надайте акт виконаних робіт:")
    await state.set_state(CompleteStates.report)


@router.message(CompleteStates.report)
async def chose_applicatin(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(report='')
    data = await state.get_data()
    await state.clear()
    application_query = update(ApplicationWorkerAssociation).where(ApplicationWorkerAssociation.application_id == data['application_id']).values(status='Ready')
    await session.execute(application_query)
    application_query = update(Application).where(Application.id == data['application_id']).values(complete_time=message.date.replace(tzinfo=None), 
                                                                                                   price=data['price'],
                                                                                                   act_name=data['report'])
    await session.execute(application_query)
    await session.commit()
    await message.answer("Заявку зачинено")


@router.message(Command("cancel"))
async def show_all_applications(message: Message, state: FSMContext, session: AsyncSession):
    application_query = (
        select(Application)
        .join(ApplicationWorkerAssociation)
        .join(Worker)
        .where(and_(Worker.user_id == str(message.from_user.id), ApplicationWorkerAssociation.status == 'Up'))
    )

    application_request = await session.execute(application_query)
    applications = [(application.address,application.id) for application in application_request.scalars()]
    
    await message.answer("Виберіть замовлення:", reply_markup=show_applications(applications))
    await state.set_state(CancelStates.application_id)


@router.callback_query(Text(startswith="chose_application"), CancelStates.application_id)
async def chose_application(callback: CallbackQuery, state: FSMContext): 
    await state.update_data(application_id=int(callback.data.split('_')[2]))
    await callback.message.answer("Вкажіть причину відмови:")
    await state.set_state(CancelStates.comment)


@router.message(CancelStates.comment)
async def cancel_application(message: Message, state: FSMContext, session: AsyncSession): 
    await state.update_data(comment=message.text)
    data = await state.get_data()
    await state.clear()

    application_query = update(ApplicationWorkerAssociation).where(ApplicationWorkerAssociation.application_id == data['application_id']).values(status='Canceled', comment=data['comment'])

    await session.execute(application_query)
    await session.commit()

    application_query = select(Application).where(Application.id == data['application_id'])
    application = (await session.execute(application_query)).scalar_one()

    message_id = application.message_id
    chat_id = config.electricity_chat_id

    text = f"🔵 Aктивно\n\n" f'{application.problem}\n\n' f'Адреса: `{application.address}`'

    await message.answer("Замовлення скасовано")
    await EditMessageText(chat_id=chat_id, message_id=message_id, text=text, reply_markup=take_application(), parse_mode='Markdown')


