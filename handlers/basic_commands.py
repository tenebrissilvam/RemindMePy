from aiogram import types


async def cmd_start(message: types.Message):
    await message.answer(
        "Этот бот поможет вам установить напоминания. Чтобы поcмотреть команды бота нажми /help."
    )


async def cmd_help(message: types.Message):
    await message.answer(
        "Доступные команды бота:\n /add_reminder : Создание нового напоминания,\n /edit_reminder : Изменение напоминания"
        "по его id, \n /delete_reminder : удаление напоминания по его id, \n /list_all : вывод всех напоминаний с их id."
    )
