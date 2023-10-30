from aiogram import Router
from aiogram.filters import Command, Text, or_f
from aiogram.types import Message, CallbackQuery
from aiogram.methods.delete_message import DeleteMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, not_, update, delete, union, desc
from datetime import timedelta, date
from collections import defaultdict
from bot.filters.chats import ChatTypeFilter
from bot.filters.admin import AdminFilter
from bot.keyboards.admins import (
    show_workers,
    make_report_navigation,
    make_worker_data_navigation,
    make_categories,
    close_free_applications,
    make_application_list
)
from bot.database.models import Application, Worker, ApplicationWorkerAssociation
from bot.config import config

status_symbol_mapping = {"Up": "⚙️", "Ready": "✔️", "Canceled": "❌"}

admin_router = Router()


@admin_router.message(
    Command("free_applications"), ChatTypeFilter(chat_type=["private"]), AdminFilter()
)
async def show_free_applications(message: Message, session: AsyncSession):
    await DeleteMessage(
        chat_id=message.chat.id, message_id=message.message_id
    )
    subquery = select(ApplicationWorkerAssociation.application_id).distinct().where(
        or_(
            ApplicationWorkerAssociation.status == "Up",
            ApplicationWorkerAssociation.status == "Ready",
        )
    )

    canceled_application_query = select(
        Application.id, Application.name, Application.address, Application.phone, Application.problem
    ).join(
        ApplicationWorkerAssociation,
        and_(
            Application.id == ApplicationWorkerAssociation.application_id,
            ApplicationWorkerAssociation.status == "Canceled",
            not_(Application.id.in_(subquery)),
        ),
    )

    free_application_query = select(
        Application.id, Application.name, Application.address, Application.phone, Application.problem
    ).where(~Application.id.in_(subquery))

    combined_query = free_application_query.union(canceled_application_query)

    applications = (await session.execute(combined_query)).all()

    if len(applications) > 0:
        text = ""
        for application in applications:
            text += f"Заявка - {application.id}:\n🏠 {application.address}\n📞 `{application.phone}`, {application.name}:\n{application.problem}\n\n"
        await message.answer(text=text, reply_markup=close_free_applications(), parse_mode="Markdown")
    else:
        await message.answer("Немає вільних заявок", parse_mode="Markdown")


@admin_router.message(
    Command("worker_status"), ChatTypeFilter(chat_type=["private"]), AdminFilter()
)
async def show_workers_list(message: Message, session: AsyncSession):
    await DeleteMessage(
        chat_id=message.chat.id, message_id=message.message_id
    )
    workers_query = select(Worker)

    workers = await session.execute(workers_query)

    workers_data = [
        (worker.name, worker.id, worker.worker_type, worker.phone) for worker in workers.scalars()
    ]

    if len(workers_data) > 0:
        await message.answer(
            "Виберіть робітника:", reply_markup=show_workers(workers_data)
        )
    else:
        await message.answer("Додайте робітників в базу")


@admin_router.message(
    or_f(Command("ban"), Command("unban")),
    ChatTypeFilter(chat_type=["private"]),
    AdminFilter(),
)
async def show_unbanned_users(message: Message, session: AsyncSession):
    blocked = False if message.text == "/ban" else True
    workers_query = select(Worker).where(Worker.blocked == blocked)

    workers = await session.execute(workers_query)

    workers_data = [
        (worker.name, worker.id, worker.worker_type) for worker in workers.scalars()
    ]

    if len(workers_data) > 0:
        await message.answer(
            "Виберіть робітника:", reply_markup=show_workers(workers_data, lock=True)
        )
    else:
        if blocked:
            await message.answer("Ви не маєте робітників, або всі вони розблоковані")
        else:
            await message.answer("Ви не маєте робітників, або всі вони заблоковані")


@admin_router.callback_query(Text(startswith="worker_data"))
async def show_worker_offset_report(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[3])
    worker_id = int(callback.data.split("_")[2])
    worker_name = callback.message.text.split(' ')[1].strip()
    worker_phone = callback.message.text.split(' ')[3].strip()
    if offset >= 0:
        application_query = (
            select(
                Application,
                ApplicationWorkerAssociation.status,
                ApplicationWorkerAssociation.comment,
            )
            .join(ApplicationWorkerAssociation)
            .join(Worker, Worker.id == ApplicationWorkerAssociation.worker_id)
            .filter(Worker.id == worker_id)
            .order_by(desc(Application.take_time))
            .limit(5)
            .offset(5 * offset)
        )
        applications = (await session.execute(application_query)).all()

        text = f'👷 {worker_name} - `{worker_phone}` звіт:\n\n'
        if len(applications) > 0:
            for application, status, comment in applications:
                text += f"Заявка - {application.id}:\n🏠 {application.address}\n📞 `{application.phone}`, {application.name}:\n"
                if status == "Up":
                    text += f'\tВ роботі з {(application.take_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")}\n\n'
                elif status == "Canceled":
                    text += f"\tВідмовився з наступної причини:\n\t\t{comment}\n\n"
                else:
                    text += f'\tЗавершенo, {(application.take_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")} - {(application.complete_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")}\n'
                    text += f"[Посилання](https://t.me/c/{str(config.channel_id)[4:]}/{application.act_id})\n\n"

            await DeleteMessage(
                chat_id=callback.message.chat.id, message_id=callback.message.message_id
            )
            await callback.message.answer(
                text=text,
                parse_mode="Markdown",
                reply_markup=make_worker_data_navigation(worker_id, offset),
            )
        else:
            await callback.answer(text="Нема старіших заявок")
    else:
        await callback.answer(text="Немає новіших заявок")


@admin_router.callback_query(Text(startswith="worker"))
async def show_worker_report(callback: CallbackQuery, session: AsyncSession):
    await DeleteMessage(
        chat_id=callback.message.chat.id, message_id=callback.message.message_id
    )
    application_query = (
        select(
            Application,
            ApplicationWorkerAssociation.status,
            ApplicationWorkerAssociation.comment,
        )
        .join(ApplicationWorkerAssociation)
        .join(Worker, Worker.id == ApplicationWorkerAssociation.worker_id)
        .filter(Worker.id == int(callback.data.split("_")[2]))
        .order_by(desc(Application.take_time))
        .limit(5)
    )
    applications = (await session.execute(application_query)).all()

    text = f'👷 {callback.data.split("_")[1]} - `{callback.data.split("_")[3]}` звіт:\n\n'
    if len(applications) > 0:
        for application, status, comment in applications:
            text += f"Заявка - {application.id}:\n🏠 {application.address}\n📞 `{application.phone}`, {application.name}:\n"
            if status == "Up":
                text += f'\tВ роботі з {(application.take_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")}\n\n'
            elif status == "Canceled":
                text += f"\tВідмовився з наступної причини:\n\t\t{comment}\n\n"
            else:
                text += f'\tЗавершенo, {(application.take_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")} - {(application.complete_time+timedelta(hours=3)).strftime("%H:%M %d.%m.%Y")}\n'
                text += f"[Посилання](https://t.me/c/{str(config.channel_id)[4:]}/{application.act_id})\n\n"
        await callback.message.answer(
            text=text,
            parse_mode="Markdown",
            reply_markup=make_worker_data_navigation(int(callback.data.split("_")[2])),
        )
    else:
        text += "\tРобіт не виконував\n"
        await callback.message.answer(text=text, parse_mode="Markdown")


@admin_router.callback_query(Text(startswith="blocked-worker"))
async def lock_worker(callback: CallbackQuery, session: AsyncSession):
    workers_query = (
        update(Worker)
        .where(Worker.id == int(callback.data.split("_")[2]))
        .values(blocked=~Worker.blocked)
    )
    await session.execute(workers_query)
    await session.commit()
    await callback.message.answer(
        text="Стан робітника змінено на протилежний", parse_mode="Markdown"
    )


@admin_router.message(
    or_f(Command("plumbing_report", "electricity_report")),
    ChatTypeFilter(chat_type=["private"]),
    AdminFilter(),
)
async def show_categories(message: Message):
    await DeleteMessage(
        chat_id=message.chat.id, message_id=message.message_id
    )
    application_type = message.text.split("_")[0][1:]
    await message.answer(text="Оберіть тип замовлень:", reply_markup=make_categories(application_type), parse_mode="Markdown")


@admin_router.callback_query(Text(startswith="category"))
async def show_report(callback: CallbackQuery, session: AsyncSession):
    application_type = callback.data.split("_")[2]
    application_status = callback.data.split("_")[1]
    application_table = Application.__table__
    worker_table = Worker.__table__

    application_query = (
        (
            select(
                Application.id,
                Application.name,
                Application.phone,
                Application.address,
                Application.problem,
                Worker.name,
                Worker.phone,
                ApplicationWorkerAssociation.status,
            )
            .select_from(
                application_table.join(ApplicationWorkerAssociation).join(worker_table)
            )
            .filter(and_(Application.application_type == application_type, ApplicationWorkerAssociation.status == application_status))
        )
        .order_by(desc(Application.take_time))
        .limit(5)
    )
    application_data = (await session.execute(application_query)).all()

    if len(application_data) > 0:
        text = ""
        for (
            application_id,
            application_name,
            application_phone,
            application_address,
            application_problem,
            worker_name,
            worker_phone,
            status,
        ) in application_data:
            text += f"Заявка - {application_id}\n🏠`{application_address}`\n📞 `{application_phone}` {application_name}\n{application_problem}\n👷 {worker_name}: `{worker_phone}` - {status_symbol_mapping[status]}\n\n"
        text += "\n\n⚙️ - в роботі\n✔️ - виконано\n❌ - відмова"
        await DeleteMessage(
            chat_id=callback.message.chat.id, message_id=callback.message.message_id
        )
        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=make_report_navigation(application_type, application_status),
        )
    else:
        await callback.message.answer("Заявки відсутні", parse_mode="Markdown")


@admin_router.callback_query(Text(startswith="report"))
async def show_offset_report(callback: CallbackQuery, session: AsyncSession):
    offset = int(callback.data.split("_")[3])
    application_type = callback.data.split("_")[1]
    application_status = callback.data.split("_")[4]
    if offset >= 0:
        application_table = Application.__table__
        worker_table = Worker.__table__

        application_query = (
            (
                select(
                    Application.id,
                    Application.name,
                    Application.phone,
                    Application.address,
                    Application.problem,
                    Worker.name,
                    Worker.phone,
                    ApplicationWorkerAssociation.status,
                )
                .select_from(
                    application_table.join(ApplicationWorkerAssociation).join(
                        worker_table
                    )
                )
                .filter(and_(Application.application_type == application_type, ApplicationWorkerAssociation.status == application_status))
            )
            .order_by(desc(Application.take_time))
            .limit(5)
            .offset(5 * offset)
        )
        application_data = (await session.execute(application_query)).all()
        if len(application_data) > 0:
            text = ""
            for (
                application_id,
                application_name,
                application_phone,
                application_address,
                application_problem,
                worker_name,
                worker_phone,
                status,
            ) in application_data:
                text += f"Заявка - {application_id}\n🏠`{application_address}`\n📞 `{application_phone}` {application_name}\n{application_problem}\n👷 {worker_name}: `{worker_phone}` - {status_symbol_mapping[status]}\n\n"
            text += "\n\n⚙️ - в роботі\n✔️ - виконано\n❌ - відмова"
            await DeleteMessage(
                chat_id=callback.message.chat.id, message_id=callback.message.message_id
            )
            await callback.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=make_report_navigation(application_type, application_status, offset),
            )
        else:
            await callback.answer(text="Нема старіших заявок")
    else:
        await callback.answer(text="Нема новіших заявок")


@admin_router.callback_query(Text("remove_message"))
async def close_report(callback: CallbackQuery):
    await DeleteMessage(
        chat_id=callback.message.chat.id, message_id=callback.message.message_id
    )


@admin_router.message(
    Command("close_application"),
    ChatTypeFilter(chat_type=["private"]),
    AdminFilter(),
)
async def show_free_list(message: Message, session: AsyncSession):
    await DeleteMessage(
        chat_id=message.chat.id, message_id=message.message_id
    )
    subquery = select(ApplicationWorkerAssociation.application_id).distinct().where(
        or_(
            ApplicationWorkerAssociation.status == "Up",
            ApplicationWorkerAssociation.status == "Ready",
        )
    )

    canceled_application_query = select(
        Application.id, Application.address, Application.application_type
    ).join(
        ApplicationWorkerAssociation,
        and_(
            Application.id == ApplicationWorkerAssociation.application_id,
            ApplicationWorkerAssociation.status == "Canceled",
            not_(Application.id.in_(subquery)),
        ),
    )

    free_application_query = select(
        Application.id, Application.address, Application.application_type
    ).where(~Application.id.in_(subquery))

    combined_query = free_application_query.union(canceled_application_query)

    applications = (await session.execute(combined_query)).all()
    applications_data = [{"id": application.id, "address": application.address, "application_type": application.application_type} for application in applications]
    await message.answer(text="Виберіть заявку:", reply_markup=make_application_list(applications_data))

@admin_router.callback_query(Text(startswith="close_application"))
async def close_application(callback: CallbackQuery, session: AsyncSession):
    await DeleteMessage(
        chat_id=callback.message.chat.id, message_id=callback.message.message_id
    )
    application_id = int(callback.data.split("_")[2])
    application_type = callback.data.split("_")[3]

    application_query = select(Application).where(Application.id==application_id)
    application = (await session.execute(application_query)).scalar_one()

    existance_query = select(ApplicationWorkerAssociation.status).where(
        (ApplicationWorkerAssociation.application_id == application_id)
    )

    existing_status = (await session.execute(existance_query)).all()

    await DeleteMessage(
        chat_id=config.plumbing_chat_id if application_type == 'plumbing' else config.electricity_chat_id,
        message_id=int(application.message_id)
    )

    if len(existing_status) > 0:
        association_query = delete(ApplicationWorkerAssociation).where(
            and_(
                ApplicationWorkerAssociation.application_id == application_id,
                ApplicationWorkerAssociation.status == "Canceled"
            )
        )
        await session.execute(association_query)
    else:
        application_query = delete(Application).where(Application.id == application_id)
        await session.execute(application_query)