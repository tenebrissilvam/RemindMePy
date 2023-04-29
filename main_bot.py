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
    text = State()


class ReminderDB:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename)
        self.create_table()

    def create_table(self):
        """
        Создание таблицы reminders, если она не существует
        """
        query = """CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    date INTEGER NOT NULL
                    );"""
        self.conn.execute(query)

    def add_reminder(self, chat_id, text, date):
        """
        Добавление нового напоминания
        """
        query = "INSERT INTO reminders (chat_id, text, date) VALUES (?, ?, ?)"
        self.conn.execute(query, (chat_id, text, date))
        self.conn.commit()

    def get_reminders_by_chat_id(self, chat_id):
        """
        Получение списка всех напоминаний для конкретного чата (отсортированы по дате)
        """
        query = "SELECT * FROM reminders WHERE chat_id=? ORDER BY date ASC"
        cursor = self.conn.execute(query, (chat_id,))
        reminders = [{"_id": row[0], "chat_id": row[1], "text": row[2], "date": row[3]} for row in cursor.fetchall()]
        return reminders

    def get_reminder_by_id(self, reminder_id):
        """
        Получение отдельного напоминания по его идентификатору
        """
        query = "SELECT * FROM reminders WHERE id=?"
        cursor = self.conn.execute(query, (reminder_id,))
        reminder = cursor.fetchone()
        if reminder:
            return {"_id": reminder[0], "chat_id": reminder[1], "text": reminder[2], "date": reminder[3]}
        else:
            return None

    def update_reminder_text(self, reminder_id, new_text):
        """
        Изменение текста существующего напоминания
        """
        query = "UPDATE reminders SET text=? WHERE id=?"
        self.conn.execute(query, (new_text, reminder_id))
        self.conn.commit()

db = ReminderDB("reminders.db")

@dp.message_handler(state=ReminderForm.text)
async def process_text(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    text = message.text
    date = datetime.datetime.now().timestamp() + REMINDER_TIMEDELTA
    db.add_reminder(chat_id, text, date)

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Напоминание '{text}' добавлено на время {datetime.datetime.fromtimestamp(date).strftime('%d.%m.%Y %H:%M:%S')}"
        )

    await state.finish()

@dp.message_handler(Command("list"))
async def cmd_list(message: types.Message, state: FSMContext):
    reminders = db.get_reminders_by_chat_id(message.chat.id)
    if len(reminders) == 0:
        await bot.send_message(chat_id=message.chat.id, text="У вас нет сохраненных напоминаний.")
        return

    msg = "Список ваших сохраненных напоминаний:\n"
    for r in reminders:
        msg += f"• {r['text']} - {datetime.datetime.fromtimestamp(r['date']).strftime('%d.%m.%Y %H:%M:%S')}\n"

    await bot.send_message(chat_id=message.chat.id, text=msg)

start_button = KeyboardButton('/start')
help_button = KeyboardButton('/help')
add_reminder = KeyboardButton('/add')
#remind_button = KeyboardButton('/remind')
list_reminder = KeyboardButton('/list')
edit_reminder = KeyboardButton('/edit')
#delete_reminder = KeyboardButton('/delete_reminder')

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row(start_button, help_button, add_reminder, edit_reminder, list_reminder)


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

'''
@dp.message_handler(Command("remind"), state="*")
async def cmd_remind(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text="Введите сообщение, которое нужно отправить:",
                           reply_markup=keyboard)
    await ReminderForm.message.set()


@dp.message_handler(state=ReminderForm.message)
async def process_message(message: types.Message, state: FSMContext):
    #create_table()
    #add_reminder(message.chat.id, message.message_id, message.text, message.time)
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

'''
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

'''
@dp.callback_query_handler(lambda c: c.data.startswith("edit_reminder"), state=ReminderForm.select_reminder)
async def process_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    reminder_id = int(callback_query.data.split(":")[1])
    reminder = get_reminder_by_id(reminder_id)

    await bot.send_message(chat_id=callback_query.from_user.id, text="Введите новый текст напоминания:")
    await ReminderForm.edit_message.set()

    async with state.proxy() as data:
        data["reminder_id"] = reminder_id
        data["text"] = reminder["text"]
bot.
'''

'''
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

'''


@dp.message_handler(state="*", content_types=types.ContentType.ANY)
async def unknown_command(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text="Извините, я не понимаю такой команды.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
