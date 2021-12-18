# @SecretSanta_bot
import telegram
import json
from environs import Env
from hashlib import sha1

from django.core.management.base import BaseCommand
from django.db.models import F
from santa_bot.models import Profile, Game
from telegram.utils import helpers

import logging
from datetime import datetime, timedelta

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

env = Env()
env.read_env()

telegram_token = env.str('TG_TOKEN')

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
ADMIN_GAME_VIEW, ADMIN_PARTICIPANTS = range(10, 12)
GUEST_COLLECT_NAME, GUEST_COLLECT_WISH, GUEST_COLLECT_MAIL, GUEST_COLLECT_LETTER, GUEST_COLLECT_END = range(20, 25)
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
    text = 'Введите название игры (не менее 7 латинских букв и цифр без пробелов)'

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
        context.user_data['price_limit'] = update.message.text

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
        context.user_data['registration_date'] = update.message.text

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
        context.user_data['gift_dispatch_date'] = update.message.text

    game_name = context.user_data['game_name']
    price_limit = context.user_data['price_limit']
    registration_date = context.user_data['registration_date']
    gift_dispatch_date = context.user_data['gift_dispatch_date']
    game_hash = sha1(game_name.encode())
    context.user_data['game_hash'] = game_hash.hexdigest()

    keyboard = [['Назад ⬅'], ['Подтвердить']]

    text = 'Подтвердите детали игры:\n' \
           f'Название игры: {game_name} \n' \
           f'Ограничение по стоимости: {price_limit} \n' \
           f'Последний день для регистрации: {registration_date} \n' \
           f'День для отправки подарков: {gift_dispatch_date} \n'
    chat_id = update.message.chat_id
    if context.user_data['price_limit'] == 'Без ограничения по стоимости':
        price_limit_status = True
    else:
        price_limit_status = False
    game = Game.objects.create(
        creator_chat_id=chat_id,
        game_hash=game_hash.hexdigest(),
        name=context.user_data['game_name'],
        price_limit_status=price_limit_status,
        price_limit=context.user_data['price_limit'],
        registration_date=context.user_data['registration_date'],
        gift_dispatch_date=context.user_data['gift_dispatch_date'],
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
    game_id = context.user_data['game_hash']
    url = helpers.create_deep_linked_url(bot.username, game_id)

    text = 'Отлично, Тайный Санта уже готовится к раздаче подарков! '\
            f'Ссылка для участия в игре: {url}'
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )


def start_santa_game(update, context):

    game_hash = context.args[0]
    context.user_data['game_hash'] = game_hash
    context.user_data['chat_id'] = update.message.chat_id
    chat_id = context.user_data['chat_id']
    game = Game.objects.all().values().get(game_hash__exact=game_hash)

    game_owner = game['creator_chat_id']
    game_name = game['name']
    context.user_data['game_name'] = game_name

    if chat_id == int(game_owner):
        keyboard = [
            ['Информация об игре'],
            ['Список участников'],
            ['Ввести данные для участия в игре']
        ]
        update.message.reply_text(
            f'Похоже, что Вы - создатель игры {game_name}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        return ADMIN_GAME_VIEW

    elif None:
        pass

    else:

        keyboard = [['Ура! Сейчас я расскажу, что хочу получить на Новый Год!']]

        update.message.reply_text(
            f'Привет! Приглашаю тебя поучаствовать в игре "Тайный Санта"!\n'
            f'Название игры: {game["name"]}\n'
            f'Подарки должны стоить: {game["price_limit"]}\n'
            f'Последний день для регистрации: {game["registration_date"]}\n'
            f'А подарочки вручим вот когда: {game["gift_dispatch_date"]}\n',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

        return GUEST_COLLECT_NAME


def collect_guest_name(update, context):
    user = update.message.from_user
    first_name = user.first_name
    context.user_data['first_name'] = first_name

    keyboard = [
        ['Ввести полное ФИО (в разаработке)'],
        ['Подтвердить'],
        ['Назад ⬅ (в разработке)']
    ]
    update.message.reply_text(
        f'Отлично. Для начала, давай познакомимся\n'
        f'Имя, взятое из твоего профиля\n'
        f'Имя: {first_name}\n',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )
    return GUEST_COLLECT_NAME


def collect_guest_name_back(update, context):
    return collect_guest_name(update, context)


def collect_guest_wish(update, context):

    keyboard = [['Назад ⬅']]

    if update.message.text != 'Назад ⬅':
        user = update.message.from_user
        first_name = user.first_name
        context.user_data['first_name'] = first_name

    update.message.reply_text(
        f'Теперь твое желание!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return GUEST_COLLECT_WISH


def collect_guest_wish_back(update, context):
    return collect_guest_wish(update, context)


def collect_guest_mail(update, context):

    keyboard = [['Назад ⬅']]

    if update.message.text != 'Назад ⬅':

        wish = update.message.text
        context.user_data['wish'] = wish

    update.message.reply_text(
        f'Введи, пожалуйста, свою электронную почту!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True)
    )

    return GUEST_COLLECT_MAIL


def collect_guest_mail_back(update, context):
    return collect_guest_mail(update, context)


def collect_guest_letter(update, context):
    keyboard = [['Назад ⬅']]

    if update.message.text != 'Назад ⬅':

        mail = update.message.text
        context.user_data['mail'] = mail

    update.message.reply_text(
        f'Как насчет коротенького послания Санте?',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True)
    )

    return GUEST_COLLECT_LETTER


def collect_guest_letter_back(update, context):
    return collect_guest_letter(update, context)


def collect_guest_end(update, context):

    keyboard = [['Назад ⬅'], ['Подтвердить']]


    if update.message.text != 'Назад ⬅':

        letter = update.message.text
        context.user_data['letter'] = letter

    chat_id = context.user_data['chat_id']  # value for db
    name = context.user_data['first_name']
    wish = context.user_data['wish']
    mail = context.user_data['mail']
    letter = context.user_data['letter']

    game = Game.objects.get(name=context.user_data['game_name'])
    actual_participants = []
    actual_participants.append(game.participants)
    actual_participants.append(chat_id)
    print(actual_participants)

    game.participants = actual_participants
    game.save()
    update.message.reply_text(
        f'Превосходно, давай еще раз все проверим! \n'
        f'Тебя зовут: {name}\n'
        f'Твое желание на Новый Год: {wish}\n'
        f'Твоя электронная почта: {mail}\n'
        f'Твое послание Санте: {letter}\n',
        reply_markup=ReplyKeyboardMarkup(
            keyboard
        )
    )

    return GUEST_COLLECT_END


def add_guest_to_database(update, context):

    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])

    chat_id = context.user_data['chat_id']
    name = context.user_data['first_name']
    wish = context.user_data['wish']
    mail = context.user_data['mail']
    letter = context.user_data['letter']
    participant, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        name = name,
        email = mail,
        wishlist = wish,
        message_for_Santa = letter,
    )

    update.message.reply_text(
        f'{game["gift_dispatch_date"]} мы проведем жеребьевку и ты узнаешь имя и контакты своего тайного друга. '
        f'Ему и нужно будет подарить подарок!',
        reply_markup=ReplyKeyboardRemove()
    )


def admin_participants(update, context):

    bot = context.bot
    game_name = context.user_data['game_name']
    url = helpers.create_deep_linked_url(bot.username, game_name)

    with open(file=f'{game_name}.json', mode='r') as file:  # replace from db
        text = json.load(file)
        game_participants = text.get('game_participants')
        if not game_participants:
            update.message.reply_text(
                f'Похоже, в игре пока никто не участвует :(\n'
                f'Поделитесь этой ссылкой с друзьями:\n'
                f'{url}',
                reply_markup=ReplyKeyboardRemove()
            )

        else:
            participants = [participant for participant in game_participants.keys()]
            num_of_participants = len(game_participants)

            keyboard = [
                ['Создать пары'],
                ['Посмотреть, кто какой подарок хочет']
            ]

            update.message.reply_text(
                f'В данный момент зарегистрировано{num_of_participants} участников, это:\n'
                f'{", ".join(participants)}',

                reply_markup=ReplyKeyboardMarkup(
                    keyboard,
                    resize_keyboard=True
                )
            )


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        updater = Updater(telegram_token)
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
                GAME_NAME: [
                    MessageHandler(Filters.regex('^[a-zA-Z0-9_].{7,99}$'), chose_game_price),
                    MessageHandler(Filters.text, chose_game_name)
                ],
                GAME_PRICE: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_name),
                    MessageHandler(Filters.text, chose_game_reg_ends)
                ],
                GAME_REG_ENDS: [
                    MessageHandler(Filters.regex(r'^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$'),
                                   chose_game_gift_date),
                    MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_price_back),

                ],
                GAME_GIFT_DATE: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_reg_ends_back),
                    MessageHandler(Filters.regex(r'^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$'),
                                   game_confirmation),
                    MessageHandler(Filters.text, chose_game_price_back)
                ],
                GAME_CONFIRMATION: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_gift_date_back),
                    MessageHandler(Filters.regex('^Подтвердить$'), send_game_url)
                ],

                # collect guest information branch
                GUEST_COLLECT_NAME: [
                    MessageHandler(Filters.regex('^Ура! Сейчас я расскажу, что хочу получить на Новый Год!$'),
                                   collect_guest_name),
                    MessageHandler(Filters.regex('^Подтвердить$'), collect_guest_wish)
                ],
                GUEST_COLLECT_WISH: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_name_back),
                    MessageHandler(Filters.text, collect_guest_mail)
                ],
                GUEST_COLLECT_MAIL: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_wish_back),
                    MessageHandler(Filters.text, collect_guest_letter)
                ],
                GUEST_COLLECT_LETTER: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_mail_back),
                    MessageHandler(Filters.text, collect_guest_end)
                ],
                GUEST_COLLECT_END: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_letter_back),
                    MessageHandler(Filters.regex('^Подтвердить$'), add_guest_to_database)
                ],

                # admin branch
                ADMIN_GAME_VIEW: [
                    MessageHandler(Filters.regex('^Список участников$'), admin_participants),
                    MessageHandler(Filters.regex('^Ввести данные для участия в игре$'), collect_guest_name)
                ]
            },
            fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
            per_user=False,
            per_chat=True
        )
        dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()