import sqlite3

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot.initializer.config_parcer import load_config
from src.keyboards import time_buttons

config = load_config("src/bot/initializer/bot.ini")
database = sqlite3.connect(config.bot.DATABASE_PATH)
cur = database.cursor()


class Start(StatesGroup):
    start = State()
    time_zone = State()


async def start_command(message: types.Message):
    await message.delete()

    cur.execute("SELECT * FROM users WHERE user_chat_id = %s" % message.chat.id)
    users_results = cur.fetchone()

    locale = message.from_user.locale
    not_in = False

    if users_results:
        await message.answer('start')
        lang_ = users_results[1]
    else:
        await message.answer('start')
        lang_ = locale.language

    if not users_results:
        users_results = [message.chat.id, lang_, None, None, None, None]

        keyboard = [message.chat.id, '❌', '❌', '❌', '❌', '❌', '❌', '❌']

        cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?);", users_results)
        cur.execute("INSERT INTO keyboard VALUES(?, ?, ?, ?, ?, ?, ?, ?);", keyboard)
        database.commit()

    database.commit()
    await Start.time_zone.set()


async def help_command(message: types.Message):
    cur.execute("SELECT * FROM users WHERE user_chat_id = %s" % message.chat.id)
    user_results = cur.fetchone()
    #
    text = 'help'
    commands = text.split(' | ')
    text = ''
    for x in commands:
        text += x + '\n'
    await message.delete()
    await message.answer(text)


async def time_zone_command(call: types.CallbackQuery):
    cur.execute("SELECT * FROM users WHERE user_chat_id = %s" % call.message.chat.id)
    user_results = cur.fetchone()
    time_zone = call.data[3::]

    cur.execute("UPDATE users SET utc_code = ? WHERE user_chat_id = ?", (time_zone, call.message.chat.id))
    database.commit()
    await call.answer()
    await Start.first()


def register_basic_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands="start", state="*")
    dp.register_message_handler(help_command, commands="help", state="*")
    dp.register_callback_query_handler(time_zone_command, state=Start.time_zone)
