from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict
from filters import ChatTypeFilter
from database import Application, Worker, ApplicationWorkerAssociation

status_symbol_mapping = {
    "Up": "⚙️",
    "Ready": "✔️",
    "Canceled": "❌"
}

router = Router()

@router.message(Command("day_report"), ChatTypeFilter(chat_type=["private"]))
async def show_all_workers(message: Message, session: AsyncSession):
    worker_query = select(ApplicationWorkerAssociation.worker_id, ApplicationWorkerAssociation.status)

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

    text+="\n\n⚙️ - в роботі\n✔️ - виконано\n❌ - відмова"

    await message.answer(text=text, parse_mode='Markdown')


@router.message(Command("worker_status"), ChatTypeFilter(chat_type=["private"]))
async def show_worker_status(message: Message, session: AsyncSession):
    worker_name = message.text.split()[1]
    application_query = select(Application, ApplicationWorkerAssociation.status, ApplicationWorkerAssociation.comment).join(ApplicationWorkerAssociation).join(Worker, Worker.id == ApplicationWorkerAssociation.worker_id).filter(Worker.name == worker_name)
    applications = (await session.execute(application_query)).all()

    text = f'{worker_name} звіт:\n\n'

    for application, status, comment in applications:
        text+=f'{application.address}:\n'
        if status == 'Up':
            text+=f'\tВ роботі\n'
        elif status == 'Canceled':
            text+=f'\tВімовився з наступної причини:\n\t\t{comment}\n'
        else:
            text+=f'\tЗавершенo, ціна:{application.price}\n'

    await message.answer(text=text, parse_mode='Markdown')