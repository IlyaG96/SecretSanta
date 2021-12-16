import logging
import os
import json

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, Filters, ConversationHandler, MessageHandler
from telegram.utils import helpers
from santa_game import start_santa_game, collect_guest_name, collect_guest_name_back, collect_guest_mail, \
    collect_guest_mail_back, collect_guest_letter, collect_guest_letter_back,  collect_guest_end, admin_participants, \
    collect_guest_wish, collect_guest_wish_back, GUEST_COLLECT_NAME, GUEST_COLLECT_WISH, GUEST_COLLECT_MAIL,\
    GUEST_COLLECT_LETTER, GUEST_COLLECT_END, ADMIN_GAME_VIEW, ADMIN_PARTICIPANTS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GAME_NAME, GAME_PRICE, GAME_REG_ENDS, GAME_BUILD, GAME_GIFT_DATE, GAME_CONFIRMATION = range(6)
SANTA_GAME = 'share-link-with-game-id'
IN_GAME = 'in-game'


def start(update, context):
    text = 'Организуй тайный обмен подарками, запусти праздничное настроение!'
    keyboard = [
        ['Создать игру']
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
    text = 'Введите название игры (не менее 8 латинских символов без цифр и пробелов)'

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )

    return GAME_NAME


def chose_game_price(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['game_name'] = update.message.text

    game_name = context.user_data['game_name']
    text = f"Для игры {game_name} будет ограничение по стоимости?"
    keyboard = [
        ['Без ограничения по стоимости'],
        ['До 500 рублей'],
        ['От 500 до 1000 рублей'],
        ['От 1000 до 2000 рублей'],
        ['Назад ⬅'],
    ]
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return GAME_PRICE


def chose_game_price_back(update, context):
    return chose_game_price(update, context)


def chose_game_reg_ends(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['game_price'] = update.message.text

    game_name = context.user_data['game_name']

    text = f'Последний день регистрации в игре {game_name} это:'
    keyboard = [
        ['25.12.2021'],
        ['31.12.2021'],
        ['Назад ⬅'],
    ]
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return GAME_REG_ENDS


def chose_game_reg_ends_back(update, context):
    return chose_game_reg_ends(update, context)


def chose_game_gift_date(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['game_reg_ends'] = update.message.text

    keyboard = [['Назад ⬅']]
    text = 'Введите день для отправки подарков в формате 29.12.2021:'

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return GAME_GIFT_DATE


def chose_game_gift_date_back(update, context):
    return chose_game_gift_date(update, context)


def game_confirmation(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['game_gift_send'] = update.message.text

    game_name = context.user_data['game_name']
    game_price = context.user_data['game_price']
    game_reg_ends = context.user_data['game_reg_ends']
    game_gift_date = context.user_data['game_gift_send']

    keyboard = [['Назад ⬅'], ['Подтвердить']]

    text = 'Подтвердите детали игры:\n' \
           f'Название игры: {game_name} \n' \
           f'Ограничение по стоимости: {game_price} \n' \
           f'Последний день для регистрации: {game_reg_ends} \n' \
           f'День для отправки подарков: {game_gift_date} \n'

    user = update.message.from_user
    first_name = user.first_name

    data = {"game_details":
        {
            "game_name": game_name,
            "game_price": game_price,
            "game_reg_ends": game_reg_ends,
            "game_gift_date": game_gift_date
        },
        "game_owner": first_name,

        "game_participants": {
            "Семен": {"pair": None, "wish": None, "mail": None, "letter": None},
            "Илья": {"pair": None, "wish": None, "mail": None, "letter": None},
            "Катерина": {"pair": None, "wish": None, "mail": None, "letter": None},
            "Лилия": {"pair": None, "wish": None, "mail": None, "letter": None}
        }
    }

    with open(file=f"{game_name}.json", mode="w") as file:
        json.dump(data, file, ensure_ascii=False)

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return GAME_CONFIRMATION


def send_game_url(update, context):
    bot = context.bot
    game_id = f"{context.user_data['game_name']}"
    url = helpers.create_deep_linked_url(bot.username, game_id)

    text = f'Ссылка для участия в игре: {url}'
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )


if __name__ == '__main__':
    load_dotenv()
    TG_TOKEN = os.getenv('TG_TOKEN')
    updater = Updater(token=TG_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_santa_game, filters=Filters.regex('^.{7,99}$')),
            CommandHandler('start', start),
        ],

        states={
            SANTA_GAME: [
                CommandHandler("start", start_santa_game, filters=Filters.regex('^.{7,20}$')),
                MessageHandler(Filters.regex('^Создать игру$'), chose_game_name),
            ],
            # build game branch
            GAME_NAME: [
                MessageHandler(Filters.text, chose_game_price)
            ],
            GAME_PRICE: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_name),
                MessageHandler(Filters.text, chose_game_reg_ends)
            ],
            GAME_REG_ENDS: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_price_back),
                MessageHandler(Filters.text, chose_game_gift_date)
            ],
            GAME_GIFT_DATE: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_reg_ends_back),
                MessageHandler(Filters.text, game_confirmation)
            ],
            GAME_CONFIRMATION: [
                MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_gift_date_back),
                MessageHandler(Filters.regex('^Подтвердить$'), send_game_url)
            ],
            # collect guest information branch
            GUEST_COLLECT_NAME: [
                MessageHandler(Filters.regex('^Ура! Сейчас я расскажу, что хочу получить на Новый Год!$'),
                               collect_guest_name)
            ],
            GUEST_COLLECT_WISH: [
                MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_name_back),
                MessageHandler(Filters.text, collect_guest_wish)
            ],
            GUEST_COLLECT_MAIL: [
                MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_wish_back),
                MessageHandler(Filters.text, collect_guest_mail)
            ],
            GUEST_COLLECT_LETTER: [
                MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_mail_back),
                MessageHandler(Filters.text, collect_guest_letter)
            ],
            GUEST_COLLECT_END: [
                MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_letter_back),
                MessageHandler(Filters.text, collect_guest_end)
            ],


            # admin branch
            ADMIN_GAME_VIEW: [
                MessageHandler(Filters.regex('^Список участников$'), admin_participants)
            ]

        },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
        per_user=False,
        per_chat=True
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
