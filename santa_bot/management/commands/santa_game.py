import logging

from telegram import ReplyKeyboardMarkup


def start_santa_game(update, context):
    game_name = context.args
    keyboard = [
        ["Ввести ФИО"]
    ]
    update.message.reply_text(
        f'Рассказать Санте о себе. А вот какие данные я перехватил: {game_name}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )
    # fix this state
    return None