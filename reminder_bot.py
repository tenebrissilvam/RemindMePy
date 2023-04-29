import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ContentType

from utils.globals import Globals
from handlers.basic_commands import cmd_help, cmd_start
from handlers.add_reminder import cmd_add_reminder
from handlers.list_all_reminders import cmd_list_all
from handlers.delete_reminder import cmd_delete_reminder
from handlers.edit_reminder import cmd_edit_reminder, process_edit_callback

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

if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(Globals.dp, skip_updates=True)
