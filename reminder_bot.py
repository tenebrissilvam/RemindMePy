from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ContentType

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from handlers.basic_commands import cmd_help, cmd_start
from handlers.add_reminder import cmd_add_reminder
from handlers.list_all_reminders import cmd_list_all
from handlers.delete_reminder import cmd_delete_reminder
from handlers.edit_reminder import cmd_edit_reminder, process_edit_callback

import logging
import smtplib

from utils.globals import Globals
from utils.ReminderDB import ReminderForm

logging.basicConfig(level=logging.INFO)


@Globals.dp.callback_query_handler(lambda c: c.data in ['edit_text', 'edit_date'])
async def process_callback_edit(callback_query: types.CallbackQuery, state: FSMContext):
    await process_edit_callback(callback_query, state)


@Globals.dp.message_handler(commands=['start'])
async def cmd_start_message(message: types.Message):
    await cmd_start(message)


@Globals.dp.message_handler(commands=['help'])
async def cmd_help_message(message: types.Message):
    await cmd_help(message)


@Globals.dp.message_handler(Command('add_reminder'))
async def process_add_reminder(message: types.Message):
    await cmd_add_reminder(message)


@Globals.dp.message_handler(Command('edit_reminder'))
async def process_edit_reminder(message: types.Message, state: FSMContext):
    await cmd_edit_reminder(message, state)


@Globals.dp.message_handler(Command('delete_reminder'))
async def process_delete_reminder(message: types.Message, state: FSMContext):
    await cmd_delete_reminder(message, state)


@Globals.dp.message_handler(Command('list_all'))
async def process_list_all(message: types.Message, state: FSMContext):
    await cmd_list_all(message, state)


@Globals.dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message, state: FSMContext):
    await message.answer(
        "Ошибка: неверная команда"
    )


@Globals.dp.message_handler(Command('register'))
async def process_register(message: types.Message, state: FSMContext):
    await cmd_register(message, state)


async def cmd_register(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    await message.answer("Введите свое имя")
    await ReminderForm.name.set()


def send_email(email, text):
    message = MIMEMultipart()
    message['From'] = Globals.EMAIL_FROM
    message['To'] = email
    message['Subject'] = 'Сообщение от RemindMePy Telegram бота'
    message.attach(MIMEText(text))

    server = smtplib.SMTP_SSL(Globals.EMAIL_SMTP_SERVER, Globals.EMAIL_SMTP_PORT)
    server.login(Globals.EMAIL_FROM, Globals.EMAIL_PASSWORD)
    server.sendmail(Globals.EMAIL_FROM, email, message.as_string())
    server.quit()


@Globals.dp.message_handler(state=ReminderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer("Введите свой email")
    await ReminderForm.email.set()


@Globals.dp.message_handler(lambda message: "@" not in message.text, state=ReminderForm.email)
async def email_invalid(message: types.Message):
    await message.reply("Введите email в правильном формате (например, example@gmail.com)")


@Globals.dp.message_handler(lambda message: "@" in message.text, state=ReminderForm.email)
async def process_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text

    Globals.db.add_user(data['name'], data['email'])

    async with state.proxy() as data:
        if 'emails' not in data:
            data['emails'] = []
        data['emails'].append(data['email'])

    await state.finish()

    await message.answer(f"Пользователь '{data['name']}' зарегистрирован и занесен в базу данных")


@Globals.dp.message_handler(Command('send'))
async def cmd_send(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'emails' not in data:
            await message.answer('Нет зарегистрированных пользователей')
            return
        email_list = data['emails']
    text = message.text.replace('/send', '')
    for email in email_list:
        send_email(email, text)
    await message.answer("Сообщения отправлены всем пользователям")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(Globals.dp, skip_updates=True)
