import logging
import asyncio

import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from aiogram.dispatcher import filters
from aiogram.types import ParseMode

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

API_TOKEN = '6297173277:AAGGVmaSBa2a5VuGZSDdX9z9s2gCiQRU5eo'
logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect('remindmepy.db')
cursor = conn.cursor()

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


class ReminderForm(StatesGroup):
    message = State()
    time = State()
    select_reminder = State()
    edit_message = State()
    FSMContext = State()

def create_table():
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                    (chat_id INT, reminder_id INT, text TEXT, time TEXT)''')
    conn.commit()

def add_reminder(chat_id: int, reminder_id: int, text: str, time: str):
    cursor.execute(f"INSERT INTO reminders VALUES ({chat_id}, {reminder_id}, '{text}', '{time}')")
    conn.commit()

def update_reminder_text(reminder_id: int, new_text:str):
    cursor.execute(f"UPDATE reminders SET text = '{new_text}' WHERE reminder_id = {reminder_id}")
    conn.commit()

def get_reminders_by_chat_id(chat_id: int):
    cursor.execute(f"SELECT * FROM reminders WHERE chat_id = {chat_id}")
    return cursor.fetchall()

def get_reminder_by_id(reminder_id: int):
    cursor.execute("SELECT * FROM reminders WHERE reminder_id = {reminder_id}")
    return cursor.fetchone()


start_button = KeyboardButton('/start')
help_button = KeyboardButton('/help')
remind_button = KeyboardButton('/remind')
all_reminder = KeyboardButton('/show_all')
edit_reminder = KeyboardButton('/edit')
delete_reminder = KeyboardButton('/delete_reminder')

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row(start_button, help_button, remind_button, edit_reminder)


@dp.message_handler(Command("start"), state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text="Привет! Это бот-напоминание.",
                           reply_markup=keyboard)


@dp.message_handler(Command("help"), state="*")
async def cmd_help(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id,
                           text="Этот бот может сохранять ваши сообщения и отправлять их в указанное время. Для этого используйте команду /remind.",
                           reply_markup=keyboard)


@dp.message_handler(Command("remind"), state="*")
async def cmd_remind(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text="Введите сообщение, которое нужно отправить:",
                           reply_markup=keyboard)
    await ReminderForm.message.set()


@dp.message_handler(state=ReminderForm.message)
async def process_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
    await bot.send_message(chat_id=message.chat.id, text="Введите дату и время в формате YYYY-MM-DD HH:MM:SS:")
    await ReminderForm.time.set()


@dp.message_handler(state=ReminderForm.time)
async def process_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['time'] = datetime.strptime(message.text, '%Y-%m-%d %H:%M:%S')

            if data['time'] < datetime.now():
                await bot.send_message(chat_id=message.chat.id, text="Ой. Время бежит незаметно, уже " + str(
                    datetime.now()) + ". Попробуйте снова")
                # data['time'] -= timedelta(hours=3)  # учитываем разницу с UTC
                return
        except ValueError:
            await bot.send_message(chat_id=message.chat.id, text="Неверный формат даты и времени.")
            return

    await bot.send_message(chat_id=message.chat.id, text="Сообщение сохранено.")
    chat_id = message.chat.id
    message_text = data['message']
    remind_time = data['time']
    await asyncio.sleep((remind_time - datetime.now()).total_seconds())
    print(remind_time)
    print(datetime.now())
    print((remind_time - datetime.now()).total_seconds())
    await bot.send_message(chat_id=chat_id, text='‼️Вспомни‼️\n' + message_text)
    await state.finish()


@dp.message_handler(Command("edit"))
async def cmd_edit(message: types.Message, state: FSMContext):
    reminders = get_reminders_by_chat_id(message.chat.id)  # список всех напоминаний
    if len(reminders) == 0:
        await bot.send_message(chat_id=message.chat.id, text="У вас нет напоминаний для редактирования.")
        return

    reminders_kb = InlineKeyboardMarkup()  # формируем клавиатуру с напоминаниями
    for r in reminders:
        reminders_kb.add(InlineKeyboardButton(text=r["text"], callback_data="edit_reminder:" + str(r["_id"])))

    await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите напоминание для редактирования:",
        reply_markup=reminders_kb
    )

    await ReminderForm.select_reminder.set()


@dp.callback_query_handler(lambda c: c.data.startswith("edit_reminder"), state=ReminderForm.select_reminder)
async def process_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    reminder_id = int(callback_query.data.split(":")[1])
    reminder = get_reminder_by_id(reminder_id)

    await bot.send_message(chat_id=callback_query.from_user.id, text="Введите новый текст напоминания:")
    await ReminderForm.edit_message.set()

    async with state.proxy() as data:
        data["reminder_id"] = reminder_id
        data["text"] = reminder["text"]


# Обработчик ввода нового текста и сохранения изменений
@dp.message_handler(state=ReminderForm.edit_message)
async def process_edit_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    reminder_id = data["reminder_id"]
    old_text = data["text"]
    new_text = message.text
    update_reminder_text(reminder_id, new_text)

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Напоминание '{old_text}' изменено на '{new_text}'"
    )

    await state.finish()


@dp.message_handler(state="*", content_types=types.ContentType.ANY)
async def unknown_command(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text="Извините, я не понимаю такой команды.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
