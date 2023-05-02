from aiogram import types
from utils.ReminderDB import ReminderForm
from utils.globals import Globals
from aiogram.dispatcher import FSMContext
import datetime
import asyncio
from handlers.states import set_reminder


async def cmd_edit_reminder(message: types.Message, state: FSMContext):
    try:
        reminder_id = int(message.text.split()[1])
    except IndexError:
        await message.answer(
            "Ошибка: необходимо передать id сообщения, которое нужно изменить"
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

    async with state.proxy() as data:
        data['reminder_id'] = reminder_id

    await message.answer(
        "Выберите, что нужно изменить:",
        reply_markup=types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Изменить текст", callback_data="edit_text"),
                types.InlineKeyboardButton(text="Изменить дату", callback_data="edit_date")
            ]
        ])
    )


async def process_edit_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder_id = data.get('reminder_id')
        edit_mode = data.get('edit_mode')

    if reminder_id is None or edit_mode != 'text':
        await message.answer(
            "Ошибка: неверный формат запроса"
        )
        await state.finish()
        return

    new_text = message.text
    Globals.db.update_reminder_text(reminder_id, new_text)

    await message.answer(
        f"Текст напоминания с id {reminder_id} изменен"
    )

    task = Globals.tasks.get(reminder_id)
    if task is not None:
        task.cancel()
        del Globals.tasks[reminder_id]

    reminder = Globals.db.get_reminder_by_id(reminder_id)
    task = asyncio.create_task(set_reminder(reminder['chat_id'], new_text, reminder['date']))
    Globals.tasks[reminder_id] = task

    await state.finish()


async def process_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    reminder_id = (await state.get_data()).get('reminder_id')

    if data == "edit_text":
        await ReminderForm.text.set()
        await callback_query.message.answer(
            "Введите новый текст напоминания"
        )
        await state.update_data({'edit_mode': 'text'})
    elif data == "edit_date":
        await ReminderForm.date.set()
        await callback_query.message.answer(
            "Введите новое время отправки напоминания в формате дд.мм.гггг чч:мм"
        )
        await state.update_data({'edit_mode': 'date'})


async def process_edit_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reminder_id = data.get('reminder_id')
        edit_mode = data.get('edit_mode')

    if reminder_id is None or edit_mode != 'date':
        await message.answer(
            "Ошибка: неверный формат запроса"
        )
        await state.finish()
        return

    now = datetime.datetime.now(Globals.TIMEZONE)
    try:
        date_str = f"{message.text}"
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        if date.timestamp() - now.timestamp() > 0:
            Globals.db.update_reminder_date(reminder_id, date.timestamp())
        else:
            await message.answer(
                "Ошибка: время напоминания должно быть позже текущего времени"
            )
            await state.finish()
            return
    except ValueError:
        await message.answer(
            "Ошибка: неверный формат даты. Введите время в формате дд.мм.гггг чч:мм"
        )
        await state.finish()
        return

    await message.answer(
        f"Дата сообщения с id {reminder_id} изменена"
    )

    task = Globals.tasks.get(reminder_id)
    if task is not None:
        task.cancel()
        del Globals.tasks[reminder_id]

    reminder = Globals.db.get_reminder_by_id(reminder_id)
    task = asyncio.create_task(set_reminder(reminder['chat_id'], reminder['text'], date.timestamp()))
    Globals.tasks[reminder_id] = task

    await state.finish()
