from aiogram import types


def time_buttons(*first):
    keyboard = types.InlineKeyboardMarkup()

    names = ['UTC−12:00', 'UTC−11:00', 'UTC−10:00', 'UTC−09:30', 'UTC−09:00', 'UTC−08:00', 'UTC−07:00', 'UTC−06:00',
             'UTC−05:00', 'UTC−04:00', 'UTC−03:30', 'UTC−03:00', 'UTC−02:00', 'UTC−01:00', 'UTC+00:00', 'UTC+01:00',
             'UTC+02:00', 'UTC+03:00', 'UTC+03:30', 'UTC+04:00', 'UTC+04:30', 'UTC+05:00', 'UTC+05:30', 'UTC+05:45',
             'UTC+06:00', 'UTC+06:30', 'UTC+07:00', 'UTC+08:00', 'UTC+08:45', 'UTC+09:00', 'UTC+09:30', 'UTC+10:00',
             'UTC+10:30', 'UTC+11:00', 'UTC+12:00', 'UTC+12:45', 'UTC+13:00', 'UTC+14:00']

    buttons = [types.InlineKeyboardButton(text=x, callback_data=x) for x in names]

    keyboard.add(*buttons)

    if not first:
        keyboard.add(types.InlineKeyboardButton(text='◀️' + 'cancel', callback_data='cancel'))
    return keyboard


def day_buttons(keyboard_results, local):
    keyboard = types.InlineKeyboardMarkup()

    buttons = [types.InlineKeyboardButton(text=keyboard_results[x + 1] + 'week' + str(x), callback_data=str(x))
               for x in range(0, 7)]

    buttons.append(types.InlineKeyboardButton(text='1️⃣' + 'onetime', callback_data="onetime"))
    buttons.append(types.InlineKeyboardButton(text='🆗' + 'ready', callback_data="ready"))
    buttons.append(types.InlineKeyboardButton(text='◀️' + 'cancel', callback_data="cancel"))
    keyboard.add(*buttons)

    return keyboard
