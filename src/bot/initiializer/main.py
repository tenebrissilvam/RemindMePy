import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

async def main(loop):
    config = load_config('/init.ini')
    open(config.bot.DATABASE_PATH, 'a+')  # reading and writing
    database = sqlite3.connect(config.bot.DATABASE_PATH)
    cursor = database.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS "user" (
    "chat_id"	INTEGER,
    "utc_code"	REAL,
    "new_reminder"	INTEGER,
    "reminder_id"	INTEGER,
    "message_id"    INTEGER,
    PRIMARY KEY("chat_id")
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS "reminders" (
    "id"	INTEGER,
    "user_chat_id"	INTEGER,
    "local_time"	TEXT,
    "local_days"	TEXT,
    "time"	TEXT,
    "text"	TEXT,
    "days"	TEXT,
    PRIMARY KEY("id")
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS "keyboard" (
    "user_chat_id"	INTEGER,
    "Monday"	TEXT,
    "Tuesday"	TEXT,
    "Wednesday"	TEXT,
    "Thursday"	TEXT,
    "Friday"	TEXT,
    "Saturday"	TEXT,
    "Sunday"	TEXT,
    PRIMARY KEY("user_chat_id")
    )''')

    database.commit()

    bot = Bot(token=config.bot.TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())

    register_handlers_common(dp)
    register_handlers_utc(dp)
    register_handlers_set_reminder(dp)
    register_handlers_my_reminders(dp)
    register_handlers_lang(dp)
    register_handlers_del_reminder(dp)
    register_handlers_edit_reminder(dp)
    asyncio.ensure_future(reminders_run.start())
    #
    await dp.start_polling()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
