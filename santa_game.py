import logging

from telegram import ReplyKeyboardMarkup



def start_santa_game(update, context):

    keyboard = [
        ["Ввести ФИО"]
    ]
    update.message.reply_text(
        "Рассказать Санте о себе",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )
    # fix this state
    return None