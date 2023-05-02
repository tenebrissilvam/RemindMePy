from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from utils.ReminderDB import ReminderDB

from pytz import timezone
import datetime


class Globals:
    TZ = timezone('Europe/Moscow')

    BOT_TOKEN = "6297173277:AAGGVmaSBa2a5VuGZSDdX9z9s2gCiQRU5eo"
    TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))
    DB_FILENAME = "reminders.db"

    bot = Bot(token=BOT_TOKEN)
    tasks = {}

    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    db = ReminderDB(DB_FILENAME)
