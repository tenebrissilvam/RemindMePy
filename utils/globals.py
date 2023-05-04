from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import datetime
from pytz import timezone

from utils.ReminderDB import ReminderDB


class Globals:
    TZ = timezone('Europe/Moscow')

    BOT_TOKEN = ""
    TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))
    DB_FILENAME = "utils/reminders.db"

    bot = Bot(token=BOT_TOKEN)
    tasks = {}

    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    db = ReminderDB(DB_FILENAME)

    edit_id = 0

    EMAIL_FROM = 'remindmepy2@gmail.com'
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 465
    EMAIL_PASSWORD = 'remindmepypythonproject2'
