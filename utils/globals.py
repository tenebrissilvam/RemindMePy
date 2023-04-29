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

from utils.ReminderDB import ReminderDB

from pytz import timezone
import datetime


class Globals:
    TZ = timezone('Europe/Moscow')

    BOT_TOKEN = "6297173277:AAGGVmaSBa2a5VuGZSDdX9z9s2gCiQRU5eo"
    TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))
    DB_FILENAME = "../reminders.db"

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    db = ReminderDB(DB_FILENAME)
