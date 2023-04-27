import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.handlers.del_reminder import register_handlers_del_reminder
from app.handlers.edit_reminder import register_handlers_edit_reminder
from app.handlers.lang import register_handlers_lang
from app.handlers.my_reminders import register_handlers_my_reminders
from app.handlers.set_reminder import register_handlers_set_reminder
from app.handlers.utc import register_handlers_utc
from datetime import datetime
from app import reminders_run