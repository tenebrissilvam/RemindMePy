import sqlite3
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


class ReminderForm(StatesGroup):
    text = State()
    date = State()


class ReminderDB:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename)
        self.create_table()

    def create_table(self):
        query = """CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    date INTEGER NOT NULL
                    );"""
        self.conn.execute(query)

    def add_reminder(self, chat_id, text, date):
        query = "INSERT INTO reminders (chat_id, text, date) VALUES (?, ?, ?)"
        self.conn.execute(query, (chat_id, text, date))
        self.conn.commit()

    def get_reminder_by_id(self, reminder_id):
        query = "SELECT * FROM reminders WHERE id=?"
        cursor = self.conn.execute(query, (reminder_id,))
        reminder = cursor.fetchone()
        if reminder:
            return {"_id": reminder[0], "chat_id": reminder[1], "text": reminder[2], "date": reminder[3]}
        else:
            return None

    def update_reminder_text(self, reminder_id, new_text):
        query = "UPDATE reminders SET text=? WHERE id=?"
        self.conn.execute(query, (new_text, reminder_id))
        self.conn.commit()

    def update_reminder_date(self, reminder_id, new_date):
        query = "UPDATE reminders SET date=? WHERE id=?"
        self.conn.execute(query, (new_date, reminder_id))
        self.conn.commit()

    def delete_reminder(self, reminder_id):
        query = "DELETE FROM reminders WHERE id=?"
        self.conn.execute(query, (reminder_id,))
        self.conn.commit()

    def get_all_reminders(self):
        query = "SELECT * FROM reminders;"
        cursor = self.conn.execute(query)
        reminders = [{"_id": row[0], "chat_id": row[1], "text": row[2], "date": row[3]} for row in cursor.fetchall()]
        return reminders
