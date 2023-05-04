from aiogram import types
from aiogram.dispatcher import FSMContext
from utils.ReminderDB import ReminderForm


async def cmd_delete_reminder(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите id напоминания, которое требуется удалить:"
    )
    await ReminderForm.delete.set()