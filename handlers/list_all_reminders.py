from aiogram import types
from utils.globals import Globals
import datetime

from aiogram.dispatcher import FSMContext

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