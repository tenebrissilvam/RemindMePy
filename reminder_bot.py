import logging
import asyncio

from aiogram import types
from aiogram.types import ParseMode
from aiogram.utils import exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ContentType

import datetime

logging.basicConfig(level=logging.INFO)

from utils.globals import Globals
from utils.ReminderDB import ReminderForm
from handlers.basic_commands import cmd_help, cmd_start

async def set_reminder(chat_id, text, date):
    now = datetime.datetime.now(Globals.TIMEZONE)
    delta = date - now.timestamp()

    if delta > 0:
        await asyncio.sleep(delta)

        try:
            await Globals.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        except exceptions.BotBlocked:
            logging.warning(f"Target [ID:{chat_id}]: blocked by user")
        except exceptions.ChatNotFound:
            logging.warning(f"Target [ID:{chat_id}]: invalid chat ID")
        except exceptions.RetryAfter as e:
            logging.warning(f"Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await set_reminder(chat_id, text, date)
        except exceptions.TelegramAPIError:
            logging.exception(f"Exception for {text} to {chat_id}")
            return False
    else:
        return False



async def cmd_add_reminder(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите текст напоминания:"
    )

    await ReminderForm.text.set()


@Globals.dp.message_handler(state=ReminderForm.text)
async def process_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

    await message.answer(
        "Введите время, когда нужно отправить напоминание в формате дд.мм.гггг чч:мм"
    )

    await ReminderForm.date.set()


@Globals.dp.message_handler(state=ReminderForm.date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        now = datetime.datetime.now(Globals.TIMEZONE)
        try:
            date_str = f"{message.text}"
            date = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            if date.timestamp() - now.timestamp() > 0:
                data['date'] = date.timestamp()
            else:
                await message.answer(
                    "Время напоминания должно быть позже текущего времени"
                )
                await state.finish()
                return
        except ValueError:
            await message.answer(
                "Неверный формат даты. Введите время в формате дд.мм.гггг чч:мм"
            )
            await state.finish()
            return

    chat_id = message.chat.id
    text = data['text']
    date = data['date']
    Globals.db.add_reminder(chat_id, text, date)

    await message.answer(
        f"Напоминание '{text}' добавлено на время {datetime.datetime.fromtimestamp(date, Globals.TZ).strftime('%d.%m.%Y %H:%M:%S')}")

    asyncio.create_task(set_reminder(chat_id, text, date))

    await state.finish()


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

    reminder = Globals.db.get_reminder_by_id(reminder_id)
    asyncio.create_task(set_reminder(reminder['chat_id'], new_text, reminder['date']))

    await state.finish()


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

    reminder = Globals.db.get_reminder_by_id(reminder_id)
    asyncio.create_task(set_reminder(reminder['chat_id'], reminder['text'], reminder['date']))

    await state.finish()


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


async def cmd_list_all(message: types.Message, state: FSMContext):
    reminders = Globals.db.get_all_reminders()

    if len(reminders) == 0:
        await message.answer(
            "Список напоминаний пуст"
        )
        return

    msg = "Список сохраненных напоминаний:\n"
    for r in reminders:
        msg += f"• id: {r['_id']}    {r['text']} - {datetime.datetime.fromtimestamp(r['date'], Globals.TZ).strftime('%d.%m.%Y %H:%M:%S')}\n"

    await message.answer(
        msg
    )


@Globals.dp.callback_query_handler(lambda c: c.data in ['edit_text', 'edit_date'])
async def process_callback_edit(callback_query: types.CallbackQuery, state: FSMContext):
    await process_edit_callback(callback_query, state)


@Globals.dp.message_handler(commands=['start'])
async def cmd_start_message(message: types.Message):
    await cmd_start(message)


@Globals.dp.message_handler(commands=['help'])
async def cmd_help_message(message: types.Message):
    await cmd_help(message)


@Globals.dp.message_handler(Command('add_reminder'))
async def process_add_reminder(message: types.Message, state: FSMContext):
    await cmd_add_reminder(message, state)


@Globals.dp.message_handler(Command('edit_reminder'))
async def process_edit_reminder(message: types.Message, state: FSMContext):
    await cmd_edit_reminder(message, state)


@Globals.dp.message_handler(Command('delete_reminder'))
async def process_delete_reminder(message: types.Message, state: FSMContext):
    await cmd_delete_reminder(message, state)


@Globals.dp.message_handler(Command('list_all'))
async def process_list_all(message: types.Message, state: FSMContext):
    await cmd_list_all(message, state)


@Globals.dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message, state: FSMContext):
    await message.answer(
        "Ошибка: неверная команда"
    )


@Globals.dp.message_handler(state=ReminderForm.text)
async def process_reminder_text(message: types.Message, state: FSMContext):
    """
    This handler is used to process the text message entered by the user when setting a reminder
    """
    # Extract the text message entered by the user
    reminder_text = message.text

    # Store the reminder text in the state so it can be used later when the reminder is sent
    await state.update_data(reminder_text=reminder_text)

    # Ask the user to select the time and date they want to be reminded at
    await message.answer(
        "When do you want to be reminded?\nPlease select the date and time in the format: dd.mm.yyyy hh:mm")


####################

'''
@dp.message_handler(commands=['edit'])
async def edit_reminder(message: types.Message):
    """
    This handler is used to edit an existing reminder.
    """
    try:
        # Ask the user for the ID of the message they want to edit
        await message.answer("Please enter the ID of the message you want to edit:")

        # Wait for the user to enter the message ID
        await ReminderForm.id.set()
    except Exception as e:
        logging.exception(e)


@Globals.dp.message_handler(commands=['delete'])
async def delete_reminder(message: types.Message):
    """
    This handler is used to delete an existing reminder.
    """
    try:
        await message.answer("Введите id сообщения, которое вы хотите удалить. Список всех сообщений с их"
                             "id можно получить при вызове команды /list_all")
        await ReminderForm.id.set()
    except Exception as e:
        logging.exception(e)


@Globals.dp.message_handler(state=ReminderForm.id)
async def process_reminder_id(message: types.Message, state: FSMContext):
    """
    This handler is used to process the message ID entered by the user.
    """
    try:
        # Extract the message ID entered by the user
        reminder_id = message.text

        # Store the message ID in the state so it can be used later when editing or deleting the reminder
        await state.update_data(reminder_id=reminder_id)

        # Ask the user whether they want to edit or delete the reminder
        await message.answer("Do you want to edit or delete the reminder?", reply_markup=edit_delete_markup)

        # Wait for the user to select an action
        await ReminderForm.action.set()
    except Exception as e:
        logging.exception(e)

'''
if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(Globals.dp, skip_updates=True)
