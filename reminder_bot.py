import logging
import sqlite3
import asyncio
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import exceptions
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ContentType

from pytz import timezone
import datetime

logging.basicConfig(level=logging.INFO)

TZ = timezone('Europe/Moscow')

BOT_TOKEN = "6297173277:AAGGVmaSBa2a5VuGZSDdX9z9s2gCiQRU5eo"
TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))
DB_FILENAME = "reminders.db"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


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

    def update_reminder_date(self, reminder_id, new_date):
        """
        Изменение даты существующего напоминания
        """
        query = "UPDATE reminders SET date=? WHERE id=?"
        self.conn.execute(query, (new_date, reminder_id))
        self.conn.commit()

    def delete_reminder(self, reminder_id):
        """
        Удаление существующего напоминания
        """
        query = "DELETE FROM reminders WHERE id=?"
        self.conn.execute(query, (reminder_id,))
        self.conn.commit()

    def get_all_reminders(self):
        """
        Получение списка всех напоминаний из БД
        """
        query = "SELECT * FROM reminders;"
        cursor = self.conn.execute(query)
        reminders = [{"_id": row[0], "chat_id": row[1], "text": row[2], "date": row[3]} for row in cursor.fetchall()]
        return reminders


db = ReminderDB(DB_FILENAME)


class ReminderForm(StatesGroup):
    text = State()
    date = State()


async def set_reminder(chat_id, text, date):
    now = datetime.datetime.now(TIMEZONE)
    delta = date - now.timestamp()

    if delta > 0:
        await asyncio.sleep(delta)

        try:
            await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        except exceptions.BotBlocked:
            logging.warning(f"Target [ID:{chat_id}]: blocked by user")
        except exceptions.ChatNotFound:
            logging.warning(f"Target [ID:{chat_id}]: invalid chat ID")
        except exceptions.RetryAfter as e:
            logging.warning(f"Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await set_reminder(chat_id, text, date)
        except exceptions.TelegramAPIError:
            logging.exception(f"Exception for {text} to {chat_id}")
            return False
    else:
        return False


async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Этот бот поможет вам установить напоминания. Чтобы добавить новое напоминание, введите команду /add_reminder."
    )

async def cmd_help(message: types.Message):
    await message.answer(
        "Доступные команды бота:\n /add_reminder, '\n, /edit_reminder, \n /delete_reminder, \n /list_all."
    )

async def cmd_add_reminder(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите текст напоминания:"
    )

    await ReminderForm.text.set()


@dp.message_handler(state=ReminderForm.text)
async def process_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

    await message.answer(
        "Введите время, когда нужно отправить напоминание в формате дд.мм.гггг чч:мм"
    )

    await ReminderForm.date.set()


@dp.message_handler(state=ReminderForm.date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        now = datetime.datetime.now(TIMEZONE)
        try:
            date_str = f"{message.text}"
            date = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            if date.timestamp() - now.timestamp() > 0:
                data['date'] = date.timestamp()
            else:
                await message.answer(
                    "Ошибка: время напоминания должно быть позже текущего времени"
                )
                await state.finish()
                return
        except ValueError:
            await message.answer(
                "Ошибка: неверный формат даты. Введите время в формате дд.мм.гггг чч:мм"
            )
            await state.finish()
            return

    chat_id = message.chat.id
    text = data['text']
    date = data['date']
    db.add_reminder(chat_id, text, date)

    await message.answer(
        f"Напоминание '{text}' добавлено на время {datetime.datetime.fromtimestamp(date, TZ).strftime('%d.%m.%Y %H:%M:%S')}"
    )

    asyncio.create_task(set_reminder(chat_id, text, date))

    await state.finish()


async def cmd_edit_reminder(message: types.Message, state: FSMContext):
    try:
        reminder_id = int(message.text.split()[1])
    except IndexError:
        await message.answer(
            "Ошибка: необходимо передать id сообщения, которое нужно изменить"
        )
        await state.finish()
        return
    except ValueError:
        await message.answer(
            "Ошибка: id сообщения должно быть числом"
        )
        await state.finish()
        return

    reminder = db.get_reminder_by_id(reminder_id)
    if reminder is None:
        await message.answer(
            "Ошибка: сообщение с таким id не найдено"
        )
        await state.finish()
        return

    async with state.proxy() as data:
        data['reminder_id'] = reminder_id

    await message.answer(
        "Выберите, что нужно изменить:",
        reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Изменить текст", callback_data="edit_text"),
                types.InlineKeyboardButton(text="Изменить дату", callback_data="edit_date")
            ]
        ])
    )


async def process_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    reminder_id = (await state.get_data()).get('reminder_id')

    if data == "edit_text":
        await ReminderForm.text.set()
        await callback_query.message.answer(
            "Введите новый текст напоминания"
        )
        await state.update_data({'edit_mode': 'text'})
    elif data == "edit_date":
        await ReminderForm.date.set()
        await callback_query.message.answer(
            "Введите новое время отправки напоминания в формате дд.мм.гггг чч:мм"
        )
        await state.update_data({'edit_mode': 'date'})


async def process_edit_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder_id = data.get('reminder_id')
        edit_mode = data.get('edit_mode')

    if reminder_id is None or edit_mode != 'text':
        await message.answer(
            "Ошибка: неверный формат запроса"
        )
        await state.finish()
        return

    new_text = message.text
    db.update_reminder_text(reminder_id, new_text)

    await message.answer(
        f"Текст напоминания с id {reminder_id} изменен"
    )

    reminder = db.get_reminder_by_id(reminder_id)
    asyncio.create_task(set_reminder(reminder['chat_id'], new_text, reminder['date']))

    await state.finish()


async def process_edit_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder_id = data.get('reminder_id')
        edit_mode = data.get('edit_mode')

    if reminder_id is None or edit_mode != 'date':
        await message.answer(
            "Ошибка: неверный формат запроса"
        )
        await state.finish()
        return

    now = datetime.datetime.now(TIMEZONE)
    try:
        date_str = f"{message.text}"
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        if date.timestamp() - now.timestamp() > 0:
            db.update_reminder_date(reminder_id, date.timestamp())
        else:
            await message.answer(
                "Ошибка: время напоминания должно быть позже текущего времени"
            )
            await state.finish()
            return
    except ValueError:
        await message.answer(
            "Ошибка: неверный формат даты. Введите время в формате дд.мм.гггг чч:мм"
        )
        await state.finish()
        return

    await message.answer(
        f"Дата сообщения с id {reminder_id} изменена"
    )

    reminder = db.get_reminder_by_id(reminder_id)
    asyncio.create_task(set_reminder(reminder['chat_id'], reminder['text'], reminder['date']))

    await state.finish()


async def cmd_delete_reminder(message: types.Message, state: FSMContext):
    try:
        reminder_id = int(message.text.split()[1])
    except IndexError:
        await message.answer(
            "Ошибка: необходимо передать id сообщения, которое нужно удалить"
        )
        await state.finish()
        return
    except ValueError:
        await message.answer(
            "Ошибка: id сообщения должно быть числом"
        )
        await state.finish()
        return

    reminder = db.get_reminder_by_id(reminder_id)
    if reminder is None:
        await message.answer(
            "Ошибка: сообщение с таким id не найдено"
        )
        await state.finish()
        return

    db.delete_reminder(reminder_id)

    await message.answer(
        f"Напоминание '{reminder['text']}' с id {reminder_id} удалено"
    )

    await state.finish()


async def cmd_list_all(message: types.Message, state: FSMContext):
    reminders = db.get_all_reminders()

    if len(reminders) == 0:
        await message.answer(
            "Список напоминаний пуст"
        )
        return

    msg = "Список сохраненных напоминаний:\n"
    for r in reminders:
        msg += f"• \#{r['_id']} {r['text']} - {datetime.datetime.fromtimestamp(r['date'], TZ).strftime('%d.%m.%Y %H:%M:%S')}\n"

    await message.answer(
        msg
    )


@dp.callback_query_handler(lambda c: c.data in ['edit_text', 'edit_date'])
async def process_callback_edit(callback_query: types.CallbackQuery, state: FSMContext):
    await process_edit_callback(callback_query, state)


@dp.message_handler(commands=['start'])
async def cmd_start_message(message: types.Message):
    await cmd_start(message)

@dp.message_handler(commands=['help'])
async def cmd_help_message(message: types.Message):
    await cmd_help(message)

@dp.message_handler(Command('add_reminder'))
async def process_add_reminder(message: types.Message, state: FSMContext):
    await cmd_add_reminder(message, state)


@dp.message_handler(Command('edit_reminder'))
async def process_edit_reminder(message: types.Message, state: FSMContext):
    await cmd_edit_reminder(message, state)


@dp.message_handler(Command('delete_reminder'))
async def process_delete_reminder(message: types.Message, state: FSMContext):
    await cmd_delete_reminder(message, state)


@dp.message_handler(Command('list_all'))
async def process_list_all(message: types.Message, state: FSMContext):
    await cmd_list_all(message, state)


@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message, state: FSMContext):
    await message.answer(
        "Ошибка: неверная команда"
    )


@dp.message_handler(state=ReminderForm.text)
async def process_reminder_text(message: types.Message, state: FSMContext):
    """
    This handler is used to process the text message entered by the user when setting a reminder
    """
    # Extract the text message entered by the user
    reminder_text = message.text

    # Store the reminder text in the state so it can be used later when the reminder is sent
    await state.update_data(reminder_text=reminder_text)

    # Ask the user to select the time and date they want to be reminded at
    await message.answer(
        "When do you want to be reminded?\nPlease select the date and time in the format: dd.mm.yyyy hh:mm")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
