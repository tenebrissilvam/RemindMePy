from aiogram import types
from utils.ReminderDB import ReminderForm


async def cmd_add_reminder(message: types.Message):
    await message.answer(
        "Введите текст напоминания:"
    )

    await ReminderForm.text.set()
