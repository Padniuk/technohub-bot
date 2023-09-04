from aiogram import Router
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import timedelta, date
from collections import defaultdict
from filters import ChatTypeFilter
from keyboards import show_workers
from database import Application, Worker, ApplicationWorkerAssociation
from config import config

status_symbol_mapping = {
    "Up": "⚙️",
    "Ready": "✔️",
    "Canceled": "❌"
}

router = Router()

@router.message(Command("day_report"), ChatTypeFilter(chat_type=["private"]))
async def show_all_workers(message: Message, session: AsyncSession):
    worker_query = select(ApplicationWorkerAssociation.worker_id, ApplicationWorkerAssociation.status).join(Application).filter(
        and_(
            Application.post_time >= date.today(),
            Application.post_time < date.today() + timedelta(days=1)
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


@router.message(Command("worker_status"), ChatTypeFilter(chat_type=["private"]))
async def show_workers_list(message: Message, session: AsyncSession):
    workers_query = select(Worker)

    workers = (await session.execute(workers_query))

    workers_data = [(worker.name,worker.id) for worker in workers.scalars()]

    await message.answer("Виберіть робітника:", reply_markup=show_workers(workers_data))


@router.callback_query(Text(startswith="worker"))
async def show_worker_report(callback: CallbackQuery, session: AsyncSession):
    application_query = select(Application, ApplicationWorkerAssociation.status, ApplicationWorkerAssociation.comment).join(ApplicationWorkerAssociation).join(Worker, Worker.id == ApplicationWorkerAssociation.worker_id).filter(and_(Worker.id == int(callback.data.split('_')[2]), Application.post_time >= date.today(), Application.post_time < date.today() + timedelta(days=1)))
    applications = (await session.execute(application_query)).all()

    text = f'{callback.data.split("_")[1]} звіт:\n\n'
    if len(applications)>0:
        for application, status, comment in applications:
            text+=f'{application.address}:\n'
            if status == 'Up':
                text+=f'\tВ роботі\n'
            elif status == 'Canceled':
                text+=f'\tВімовився з наступної причини:\n\t\t{comment}\n'
            else:
                text+=f'\tЗавершенo, [Посилання](https://t.me/c/{str(config.channel_id)[4:]}/{application.act_name})\n'
        await callback.message.answer(text=text, parse_mode='Markdown')
    else:
        text+='\tРобіт не виконував\n'
        await callback.message.answer(text=text, parse_mode='Markdown')