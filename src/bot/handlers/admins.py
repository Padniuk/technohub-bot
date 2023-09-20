from aiogram import Router
from aiogram.filters import Command, Text, or_f
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from datetime import timedelta, date
from collections import defaultdict
from bot.filters.chats import ChatTypeFilter
from bot.filters.admin import AdminFilter
from bot.keyboards.admins import show_workers
from bot.database.models import Application, Worker, ApplicationWorkerAssociation
from bot.config import config

status_symbol_mapping = {
    "Up": "⚙️",
    "Ready": "✔️",
    "Canceled": "❌"
}

admin_router = Router()

@admin_router.message(Command("plumbing_day_report"), ChatTypeFilter(chat_type=["private"]), AdminFilter())
async def show_all_plumbers(message: Message, session: AsyncSession):
    worker_query = select(ApplicationWorkerAssociation.worker_id, ApplicationWorkerAssociation.status).join(Application).filter(
        and_(
            Application.post_time >= date.today(),
            Application.post_time < date.today() + timedelta(days=1),
            Application.application_type == 'plumbing'
        )
    )

    workers = (await session.execute(worker_query)).all()

    worker_statuses = defaultdict(list)
    for worker_id, application_status in workers:
        worker = (await session.execute(select(Worker).where(Worker.id == worker_id))).scalar_one()
        worker_name = worker.name
        worker_statuses[worker_name].append(status_symbol_mapping.get(application_status, application_status))

    text = ""
    for worker_name, statuses in worker_statuses.items():
        formatted_statuses = ' - '.join(statuses)
        text += f"`{worker_name}`: {formatted_statuses}\n"
    if len(text)>0:
        text+="\n\n⚙️ - в роботі\n✔️ - виконано\n❌ - відмова"
        await message.answer(text=text, parse_mode='Markdown')
    else:
        await message.answer(text="Замовлень по сантехніці немає", parse_mode='Markdown')

@admin_router.message(Command("electricity_day_report"), ChatTypeFilter(chat_type=["private"]), AdminFilter())
async def show_all_electricers(message: Message, session: AsyncSession):
    worker_query = select(ApplicationWorkerAssociation.worker_id, ApplicationWorkerAssociation.status).join(Application).filter(
        and_(
            Application.post_time >= date.today(),
            Application.post_time < date.today() + timedelta(days=1),
            Application.application_type == 'electricity'
        )
    )

    workers = (await session.execute(worker_query)).all()

    worker_statuses = defaultdict(list)
    for worker_id, application_status in workers:
        worker = (await session.execute(select(Worker).where(Worker.id == worker_id))).scalar_one()
        worker_name = worker.name
        worker_statuses[worker_name].append(status_symbol_mapping.get(application_status, application_status))

    text = ""
    for worker_name, statuses in worker_statuses.items():
        formatted_statuses = ' - '.join(statuses)
        text += f"`{worker_name}`: {formatted_statuses}\n"
    if len(text)>0:
        text+="\n\n⚙️ - в роботі\n✔️ - виконано\n❌ - відмова"
        await message.answer(text=text, parse_mode='Markdown')
    else:
        await message.answer(text="Замовлень по електриці немає", parse_mode='Markdown')

@admin_router.message(Command("free_applications"), ChatTypeFilter(chat_type=["private"]), AdminFilter())
async def show_free_list(message: Message, session: AsyncSession):
    subquery = select(ApplicationWorkerAssociation.application_id).distinct()

    free_application_query = select(Application.name, Application.address, Application.phone, Application.problem).where(
        and_(
            ~Application.id.in_(subquery),
            Application.post_time >= date.today(), 
            Application.post_time < date.today() + timedelta(days=1)
        )
    )

    canceled_application_query = select(Application.name, Application.address, Application.phone, Application.problem).join(
        ApplicationWorkerAssociation,
        and_(
            Application.id == ApplicationWorkerAssociation.application_id,
            ApplicationWorkerAssociation.status == 'Canceled'
        )
    ).where(
        and_(
            Application.post_time >= date.today(),
            Application.post_time < date.today() + timedelta(days=1)
        )
    )

    combined_query = free_application_query.union(canceled_application_query)

    applications = (await session.execute(combined_query)).all()
    
    if len(applications)>0:
        text=''
        for application in applications:
            text+=f'`{application.address}` - {application.name}, `{application.phone}`\n{application.problem}\n\n'
        await message.answer(text=text, parse_mode='Markdown')
    else:
        await message.answer("Немає вільних заявок", parse_mode='Markdown')


@admin_router.message(Command("worker_status"), ChatTypeFilter(chat_type=["private"]), AdminFilter())
async def show_workers_list(message: Message, session: AsyncSession):
    workers_query = select(Worker)

    workers = (await session.execute(workers_query))

    workers_data = [(worker.name,worker.id, worker.worker_type) for worker in workers.scalars()]

    if len(workers_data)>0:
        await message.answer("Виберіть робітника:", reply_markup=show_workers(workers_data))
    else:
        await message.answer("Додайте робітників в базу")

@admin_router.message(or_f(Command("ban"), Command("unban")), ChatTypeFilter(chat_type=["private"]), AdminFilter())
async def show_unbanned_users(message: Message, session: AsyncSession):
    blocked = False if message.text == '/ban' else True
    workers_query = select(Worker).where(Worker.blocked==blocked)

    workers = (await session.execute(workers_query))

    workers_data = [(worker.name,worker.id, worker.worker_type) for worker in workers.scalars()]

    if len(workers_data)>0:
        await message.answer("Виберіть робітника:", reply_markup=show_workers(workers_data, lock=True))
    else:
        if blocked:
            await message.answer("Ви не маєте робітників, або всі вони розблоковані")
        else:
            await message.answer("Ви не маєте робітників, або всі вони заблоковані")


@admin_router.callback_query(Text(startswith="worker"))
async def show_worker_report(callback: CallbackQuery, session: AsyncSession):
    application_query = select(Application, ApplicationWorkerAssociation.status, ApplicationWorkerAssociation.comment).join(ApplicationWorkerAssociation).join(Worker, Worker.id == ApplicationWorkerAssociation.worker_id).filter(and_(Worker.id == int(callback.data.split('_')[2]), Application.post_time >= date.today(), Application.post_time < date.today() + timedelta(days=1)))
    applications = (await session.execute(application_query)).all()

    text = f'{callback.data.split("_")[1]} звіт:\n\n'
    if len(applications)>0:
        for application, status, comment in applications:
            text+=f'{application.id} - {application.address}, {application.name}, `{application.phone}`:\n'
            if status == 'Up':
                text+=f'\tВ роботі\n'
            elif status == 'Canceled':
                text+=f'\tВімовився з наступної причини:\n\t\t{comment}\n'
            else:
                text+=f'\tЗавершенo, [Посилання](https://t.me/c/{str(config.channel_id)[4:]}/{application.act_id})\n'
        await callback.message.answer(text=text, parse_mode='Markdown')
    else:
        text+='\tРобіт не виконував\n'
        await callback.message.answer(text=text, parse_mode='Markdown')

@admin_router.callback_query(Text(startswith="blocked-worker"))
async def lock_worker(callback: CallbackQuery, session: AsyncSession):
    workers_query = update(Worker).where(Worker.id == int(callback.data.split('_')[2])).values(blocked=~Worker.blocked)
    await session.execute(workers_query)
    await session.commit()
    await callback.message.answer(text='Стан робітника змінено на протилежний', parse_mode='Markdown')