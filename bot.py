import logging
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    Filters,
    ConversationHandler,
    MessageHandler
)

from telegram.utils import helpers

from santa_game import start_santa_game

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

GAME_NAME, GAME_PRICE, GAME_REG_ENDS, GAME_BUILD, GAME_GIFT_DATE, GAME_CONFIRMATION = range(6)
SANTA_GAME = "share-link-with-game-id"
IN_GAME = "in-game"


def start(update, context):

    bot = context.bot
    url = helpers.create_deep_linked_url(bot.username, "params")
    text = f"Организуй тайный обмен подарками, запусти праздничное настроение!:\n\n + {url}"
    keyboard = [
        ["Создать игру"]
    ]
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return SANTA_GAME


def chose_game_name(update, context):

    update.message.reply_text(
        "Введите название игры",
        reply_markup=ReplyKeyboardRemove)

    return GAME_NAME


def chose_game_price(update, context):

    if update.message.text != 'Назад ⬅':

        game_name = update.message.text
        context.user_data['game_name'] = game_name
        text = f"Для игры {game_name} будет ограничение по стоимости?"
        keyboard = [
            ["Без ограничения по стоимости"],
            ["До 500 рублей"],
            ["От 500 до 1000 рублей"],
            ["От 1000 до 2000 рублей"]
        ]
        update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

    return GAME_PRICE


def chose_game_reg_ends(update, context):

    if update.message.text != 'Назад ⬅':

        game_price = update.message.text
        context.user_data['game_price'] = game_price

        game_name = context.user_data['game_name']

        text = f"Последний день регистрации в игре {game_name} это:"
        keyboard = [
            ["25.12.2021"],
            ["31.12.2021"],
        ]
        update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

    return GAME_REG_ENDS


def chose_game_gift_date(update, context):

    if update.message.text != 'Назад ⬅':

        game_reg_ends = update.message.text
        context.user_data['game_reg_ends'] = game_reg_ends

        game_name = context.user_data['game_name']

        text = f"Последний день регистрации в игре {game_name} это:"
        keyboard = [
            ["25.12.2021"],
            ["31.12.2021"],
        ]
        update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

    return GAME_GIFT_DATE


if __name__ == '__main__':
    load_dotenv()
    TG_TOKEN = os.getenv("TG_TOKEN")
    updater = Updater(token=TG_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Начать$'), start), CommandHandler("start", start)],
        states={
            SANTA_GAME: [
                CommandHandler("start", start_santa_game, filters=Filters.regex('params')),
                MessageHandler(Filters.regex('^Создать игру$'), chose_game_name),
            ],
            GAME_NAME: [
                MessageHandler(Filters.text, chose_game_price)
            ],
            GAME_PRICE: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_name),
                MessageHandler(Filters.text, chose_game_reg_ends)
            ],
            GAME_REG_ENDS: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_price),
                MessageHandler(Filters.text, chose_game_gift_date)
            ]


        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
        per_user=False,
        per_chat=True
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()