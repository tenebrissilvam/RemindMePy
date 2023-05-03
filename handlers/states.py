from aiogram import types
from utils.ReminderDB import ReminderForm
from aiogram.dispatcher import FSMContext
from utils.globals import Globals
import datetime
import asyncio
import logging
from aiogram.types import ParseMode
from aiogram.utils import exceptions


async def set_reminder(chat_id, text, date):
    now = datetime.datetime.now(Globals.TIMEZONE)
    delta = date - now.timestamp()

    if delta > 0:
        await asyncio.sleep(delta)

        try:
            await Globals.bot.send_message(chat_id, '‼️ ' + text + ' ‼️', parse_mode=ParseMode.HTML)
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

    task = asyncio.create_task(set_reminder(chat_id, text, date))

    reminders = Globals.db.get_all_reminders()
    if len(reminders) != 0:
        reminder_id = reminders[-1]['_id']
        Globals.tasks[reminder_id] = task

    await state.finish()


@Globals.dp.message_handler(state=ReminderForm.delete)
async def process_delete(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = int(message.text)

    try:
        reminder_id = data['id']
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

    if datetime.datetime.now(Globals.TIMEZONE).timestamp() < reminder['date']:

        task = Globals.tasks[reminder_id]
        if task is not None:
            task.cancel()
            del Globals.tasks[reminder_id]

    await state.finish()
