import asyncio
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config_parcer import load_config

from src.bot.comand_handlers.basic_commands import register_basic_handlers
#from app.handlers.del_reminder import register_handlers_del_reminder
#from app.handlers.edit_reminder import register_handlers_edit_reminder
#from app.handlers.lang import register_handlers_lang
#from app.handlers.my_reminders import register_handlers_my_reminders
from src.bot.comand_handlers.new_reminder import register_handlers_set_reminder
#from app.handlers.utc import register_handlers_utc
from datetime import datetime
from src.bot import exec_reminder


async def main(loop):
    config = load_config("src/bot/initializer/bot.ini")
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

    register_basic_handlers(dp)
    #register_handlers_utc(dp)
    register_handlers_set_reminder(dp)
    #register_handlers_my_reminders(dp)
    #register_handlers_lang(dp)
    #register_handlers_del_reminder(dp)
    #register_handlers_edit_reminder(dp)
    asyncio.ensure_future(exec_reminder.start())
    #
    await dp.start_polling()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
