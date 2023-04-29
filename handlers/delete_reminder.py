from aiogram import types
from utils.globals import Globals
from aiogram.dispatcher import FSMContext


async def cmd_delete_reminder(message: types.Message, state: FSMContext):
    try:
        reminder_id = int(message.text.split()[1])
    except IndexError:
        await message.answer(
            "Ошибка: необходимо передать id сообщения, которое нужно удалить"
        )
        await state.finish()
        return
    except ValueError:
        await message.answer(
            "Ошибка: id сообщения должно быть числом"
        )
        await state.finish()
        return

    reminder = Globals.db.get_reminder_by_id(reminder_id)
    if reminder is None:
        await message.answer(
            "Ошибка: сообщение с таким id не найдено"
        )
        await state.finish()
        return

    Globals.db.delete_reminder(reminder_id)

    await message.answer(
        f"Напоминание '{reminder['text']}' с id {reminder_id} удалено"
    )

    await state.finish()
