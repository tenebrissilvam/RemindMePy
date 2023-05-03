import sqlite3
from aiogram.dispatcher.filters.state import State, StatesGroup


class ReminderForm(StatesGroup):
    text = State()
    date = State()
    delete = State()
    edit = State()
    fill_in_id = State()
    edit_text = State()
    edit_date = State()
    name = State()
    email = State()

class RunningTasks:
    tasks = {}


class ReminderDB:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename)
        self.create_table()
        self.create_user_table()

    def create_table(self):
        query = """CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    date INTEGER NOT NULL
                    );"""
        self.conn.execute(query)

    def create_user_table(self):
        query = """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name INTEGER NOT NULL,
                    email TEXT NOT NULL
                    );"""
        self.conn.execute(query)

    def add_user(self, name, email):
        query = "INSERT INTO users (name, email) VALUES (?, ?, ?)"
        self.conn.execute(query, (name, email))
        self.conn.commit()

    def get_email_by_name(self, name):
        query = "SELECT * FROM users WHERE name=?"
        cursor = self.conn.execute(query, (name,))
        user = cursor.fetchone()
        if user:
            return user[2]
        else:
            return None

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
