# @SecretSanta_bot
from environs import Env

from django.core.management.base import BaseCommand
from django.db.models import F
from santa_bot.models import Profile, Game

import logging
from datetime import datetime, timedelta

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from .santa_game import start_santa_game

env = Env()
env.read_env()

telegram_token = env.str('TG_TOKEN')


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    GAME_NAME,
    GAME_PRICE,
    GAME_REG_ENDS,
    GAME_BUILD,
    GAME_GIFT_DATE,
    GAME_CONFIRMATION,
) = range(6)
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
    text = 'Введите название игры (не менее 7 латинских символов без цифр и пробелов)'

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
        ['2021-12-25'],
        ['2021-12-31'],
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
    text = 'Введите день для отправки подарков в формате 2021-12-29:'

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
    chat_id = update.message.chat_id
    participant, _ = Profile.objects.get_or_create(external_id=chat_id)
    if context.user_data['game_price'] == 'Без ограничения по стоимости':
        price_limit_status = True
    game = Game.objects.create(
        profile=participant,
        name=context.user_data['game_name'],
        price_limit_status=price_limit_status,
        price_limit=context.user_data['game_price'],
        registration_date=context.user_data['game_reg_ends'],
        gift_dispatch_date=context.user_data['game_gift_send'],
    )
    game.save
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


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        # Create the Updater and pass it your bot's token.
        updater = Updater(telegram_token)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add conversation handler with the states CHOICE, TITLE, PHOTO, CONTACT, LOCATION
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                SANTA_GAME: [
                    CommandHandler("start", start_santa_game, filters=Filters.regex('^.{7,20}$')),
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
                ]
            },
            fallbacks=[CommandHandler('start', start),
                       MessageHandler(Filters.regex('^Начать$'), start)],
            allow_reentry=True,
        )

        dispatcher.add_handler(conv_handler)
        #dispatcher.add_error_handler(error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()