import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, KeyboardButton, ReplyKeyboardMarkup
from datetime import datetime, timedelta

API_TOKEN = '6297173277:AAGGVmaSBa2a5VuGZSDdX9z9s2gCiQRU5eo'
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


class ReminderForm(StatesGroup):
    message = State()
    time = State()


start_button = KeyboardButton('/start')
help_button = KeyboardButton('/help')
remind_button = KeyboardButton('/remind')

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row(start_button, help_button, remind_button)


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
    await bot.send_message(chat_id=chat_id, text='‼️Reminder‼️\n' + message_text)
    await state.finish()


@dp.message_handler(state="*", content_types=types.ContentType.ANY)
async def unknown_command(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.chat.id, text="Извините, я не понимаю такой команды.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
