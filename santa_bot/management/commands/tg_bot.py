# @SecretSanta_bot
import telegram
import re
from datetime import datetime
from environs import Env
from hashlib import sha1

from django.core.management.base import BaseCommand
from santa_bot.models import Profile, Game
from telegram.utils import helpers

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

env = Env()
env.read_env()

telegram_token = env.str('TG_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GAME_NAME, GAME_PRICE, GAME_REG_ENDS, GAME_BUILD, GAME_GIFT_DATE, GAME_CONFIRMATION = range(6)
REGISTERED_GAME_VIEW, ADMIN_PARTICIPANTS, REGISTERED_CORRECT_DATA, \
REGISTERED_CORRECT_NAME_ACCEPT, REGISTERED_CORRECT_WISH_ACCEPT, \
REGISTERED_CORRECT_EMAIL_ACCEPT, REGISTERED_CORRECT_LETTER_ACCEPT = range(10, 17)
GUEST_COLLECT_NAME, GUEST_COLLECT_WISH, GUEST_COLLECT_MAIL, GUEST_COLLECT_LETTER, GUEST_COLLECT_END = range(20, 25)
SANTA_GAME = 'share-link-with-game-id'


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
    text = 'Введите название игры'

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )

    return GAME_NAME


def chose_game_price(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['game_name'] = update.message.text
        try:
            game = Game.objects.all().values().get(name__exact=context.user_data['game_name'])
        except Exception:
            game = None
        if game:
            game_name = context.user_data['game_name']
            update.message.reply_text(
                f'Похоже название "{game_name}" уже занято. Попробуйте ввести другое'
            )
            return chose_game_name(update, context)

    game_name = context.user_data['game_name']
    text = f"Для игры '{game_name}' будет ограничение по стоимости?"
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

    text = f'Последний день регистрации в игре "{game_name}" это:'
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
    if update.message.text != 'Назад ⬅' and\
            re.match("\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])*", update.message.text):
        context.user_data['registration_date'] = update.message.text

    keyboard = [['Назад ⬅']]
    text = f'Введите день, в который планируется дарить подарки, в формате 2021-12-29:\n' \
           f'Помните, что день, в который планируется дарить подарки, должен наступить позже дня ' \
           f'окончания регистрации {context.user_data["registration_date"]}'

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

        if update.message.text < context.user_data['registration_date']:
            return chose_game_gift_date(update, context)

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

    text = 'Отлично, Тайный Санта уже готовится к раздаче подарков! ' \
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

    game_name = game['name']
    context.user_data['game_name'] = game_name

    if str(chat_id) in game['participants']:
        keyboard = [
            ['Информация об игре'],
            ['Просмотреть виш-листы других участников'],
            ['Хочу поменять информацию о себе'],
        ]
        update.message.reply_text(
            f'Похоже, что ты уже зарегистрирован в игре {game_name}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        return REGISTERED_GAME_VIEW

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
        ['Подтвердить'],
    ]
    update.message.reply_text(
        f'Отлично. Для начала, давай познакомимся\n'
        f'Имя, взятое из твоего профиля\n'
        f'{first_name}\n'
        f'Если это не ты, то напиши свое имя и отправь его',
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
        if update.message.text != 'Подтвердить':
            first_name = update.message.text
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

    name = context.user_data['first_name']
    wish = context.user_data['wish']
    mail = context.user_data['mail']
    letter = context.user_data['letter']

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
    game = Game.objects.get(game_hash=context.user_data['game_hash'])

    chat_id = context.user_data['chat_id']
    name = context.user_data['first_name']
    wish = context.user_data['wish']
    mail = context.user_data['mail']
    letter = context.user_data['letter']
    participant, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        name=name,
        email=mail,
        wishlist=wish,
        message_for_Santa=letter,
    )

    game.participants.update({
        chat_id: {"name": name, "email": mail, "wishlist": wish, "message_for_Santa": letter
                  }})
    game.save()

    update.message.reply_text(
        f'{game.registration_date} мы проведем жеребьевку, и ты узнаешь имя и контакты своего тайного друга. '
        f'Ему и нужно будет подарить подарок!',
        reply_markup=ReplyKeyboardRemove()
    )


def registered_game_display(update, context):
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    keyboard = [
        ['Просмотреть виш-листы других участников'],
        ['Хочу поменять информацию о себе'],
    ]
    update.message.reply_text(
        f'Информация об игре "Тайный Санта"\n'
        f'Название твоей игры: {game["name"]}\n'
        f'Подарки должны стоить: {game["price_limit"]}\n'
        f'Последний день для регистрации: {game["registration_date"]}\n'
        f'А подарочки вручим вот когда: {game["gift_dispatch_date"]}\n',

        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return REGISTERED_GAME_VIEW


def registered_participants(update, context):
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    keyboard = [['Назад ⬅']]
    participants = game['participants'].keys()
    for participant in participants:
        wish = game['participants'][participant]["wishlist"]
        update.message.reply_text(
            f'А вот и пожелания участников:\n'
            f'Участник "{participant["name"]}" хочет "{wish}" \n',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

    return REGISTERED_GAME_VIEW


def correct_guest_data(update, context):
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    keyboard = [['Назад ⬅'],
                ['Исправить имя'],
                ['Исправить желание'],
                ['Исправить e-mail'],
                ['Исправить письмо Санте']]
    chat_id = str(context.user_data['chat_id'])
    participant = game['participants'][chat_id]

    name = participant['name']
    wishlist = participant['wishlist']
    email = participant['email']
    message_for_Santa = participant['message_for_Santa']

    update.message.reply_text(
        f'Сейчас о тебе сохранены следующие данные:\n'
        f'Тебя зовут: {name}\n'
        f'Твое желание на Новый Год: {wishlist}\n'
        f'Твоя электронная почта: {email}\n'
        f'Твое послание Санте: {message_for_Santa}\n',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ))

    return REGISTERED_CORRECT_DATA


def correct_name(update, context):
    keyboard = [['Назад ⬅']]
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    participant = game['participants'][chat_id]
    name = participant['name']
    update.message.reply_text(
        f'Исправлю имя без регистрации и смс. Только для тебя:\n'
        f'Текущее имя: {name} \n'
        f'Напечатай, пожалуйста, новое имя:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ))

    return REGISTERED_CORRECT_NAME_ACCEPT


def rewrite_name(update, context):
    new_name = update.message.text
    game = Game.objects.get(game_hash=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    profile = Profile.objects.get(external_id=chat_id)
    profile.name = new_name
    profile.save()
    game.participants[chat_id]['name'] = new_name
    game.save()

    return correct_guest_data(update, context)


def correct_wishlist(update, context):
    keyboard = [['Назад ⬅']]
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    participant = game['participants'][chat_id]
    wishlist = participant['wishlist']

    update.message.reply_text(
        f'Текущее желание: {wishlist} \n'
        f'Напечатай, пожалуйста, новое:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ))

    return REGISTERED_CORRECT_WISH_ACCEPT


def rewrite_wishlist(update, context):
    new_wishlist = update.message.text
    game = Game.objects.get(game_hash=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    game.participants[chat_id]['wishlist'] = new_wishlist
    game.save()
    profile = Profile.objects.get(external_id=chat_id)
    profile.wishlist = new_wishlist
    profile.save()
    return correct_guest_data(update, context)


def correct_email(update, context):
    keyboard = [['Назад ⬅']]
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    participant = game['participants'][chat_id]
    email = participant['email']
    update.message.reply_text(
        f'Текущий e-mail: {email} \n'
        f'Напечатай, пожалуйста, новый:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ))

    return REGISTERED_CORRECT_EMAIL_ACCEPT


def rewrite_email(update, context):
    new_email = update.message.text
    game = Game.objects.get(game_hash=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    game.participants[chat_id]['email'] = new_email
    game.save()
    profile = Profile.objects.get(external_id=chat_id)
    profile.email = new_email
    profile.save()

    return correct_guest_data(update, context)


def correct_letter(update, context):
    keyboard = [['Назад ⬅']]
    game = Game.objects.all().values().get(game_hash__exact=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    participant = game['participants'][chat_id]
    message_for_Santa = participant['message_for_Santa']
    update.message.reply_text(
        f'Текущее послание Санте: {message_for_Santa} \n'
        f'Напечатай, пожалуйста, новое:',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ))

    return REGISTERED_CORRECT_LETTER_ACCEPT


def rewrite_letter(update, context):
    new_message_for_Santa = update.message.text
    game = Game.objects.get(game_hash=context.user_data['game_hash'])
    chat_id = str(context.user_data['chat_id'])
    game.participants[chat_id]['message_for_Santa'] = new_message_for_Santa
    game.save()
    profile = Profile.objects.get(external_id=chat_id)
    profile.message_for_Santa = new_message_for_Santa
    profile.save()

    return correct_guest_data(update, context)


def send_messages(raffle_pairs):
    bot = telegram.Bot(token=telegram_token)
    if raffle_pairs[1] != 'Одиночество - изнанка свободы.':
        for participant1, participant2 in raffle_pairs.items():
            first_participant = Profile.objects.get(external_id=participant1)
            second_participant = Profile.objects.get(external_id=participant2)
            bot.send_message(chat_id=participant1,
                             text='Жеребьевка в игре “Тайный Санта” проведена! \n'
                                  'Спешу сообщить кто тебе выпал: \n'
                                  f'Имя: {second_participant.name} \n'
                                  f'Почта:{second_participant.email} \n'
                                  f'Интересы: {second_participant.wishlist} \n'
                                  f'Письмо Санте: {second_participant.message_for_Santa} \n'
                             )
            bot.send_message(chat_id=participant2,
                             text='Жеребьевка в игре “Тайный Санта” проведена! \n'
                                  'Спешу сообщить кто тебе выпал: \n'
                                  f'Имя: {first_participant.name} \n'
                                  f'Почта:{first_participant.email} \n'
                                  f'Интересы: {first_participant.wishlist} \n'
                                  f'Письмо Санте: {first_participant.message_for_Santa} \n'
                             )
    else:
        bot.send_message(chat_id=raffle_pairs[0],
                         text='Вы одни участвуете в игре. Купите себе самый лучший подарок')

def perform_raffle():
    games = Game.objects.all()
    for game in games:
        registration_date = game.registration_date.strftime("%Y-%m-%d")
        actual_date = datetime.now().strftime("%Y-%m-%d")
        if registration_date == actual_date:
            all_participant = list(game.participants.keys())
            participant_quantity = len(all_participant)
            if participant_quantity != 1:
                remains = participant_quantity % 2
                if remains == 0:
                    half_of_participant_quantity = participant_quantity // 2
                    first_half_of_participants = all_participant[:half_of_participant_quantity]
                    second_half_of_participants = all_participant[half_of_participant_quantity:]
                    raffle_pairs = dict(zip(first_half_of_participants, second_half_of_participants))
                    send_messages(raffle_pairs)
                else:
                    half_of_participant_quantity = participant_quantity // 2
                    first_half_of_participants = all_participant[:half_of_participant_quantity]
                    second_half_of_participants = all_participant[half_of_participant_quantity:]
                    raffle_pairs = dict(zip(first_half_of_participants, second_half_of_participants))
                    raffle_pairs[all_participant[-1]] = all_participant[0]
                    send_messages(raffle_pairs)
            else:
                all_participant.append('Одиночество - изнанка свободы.')
                send_messages(all_participant)



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
                    MessageHandler(Filters.regex('^.{1,99}$'), chose_game_price),
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
                    MessageHandler(Filters.text, chose_game_gift_date_back)
                ],
                GAME_CONFIRMATION: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), chose_game_gift_date_back),
                    MessageHandler(Filters.regex('^Подтвердить$'), send_game_url)
                ],

                # collect guest information branch
                GUEST_COLLECT_NAME: [
                    MessageHandler(Filters.regex('^Ура! Сейчас я расскажу, что хочу получить на Новый Год!$'),
                                   collect_guest_name),
                    MessageHandler(Filters.regex('^Подтвердить$'), collect_guest_wish),
                    MessageHandler(Filters.regex(r'[а-яА-Я]{2,40}$'), collect_guest_wish)
                ],
                GUEST_COLLECT_WISH: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_name_back),
                    MessageHandler(Filters.text, collect_guest_mail)
                ],
                GUEST_COLLECT_MAIL: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_wish_back),
                    MessageHandler(Filters.regex(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                                   collect_guest_letter),
                    MessageHandler(Filters.text, collect_guest_mail),
                ],
                GUEST_COLLECT_LETTER: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_mail_back),
                    MessageHandler(Filters.text, collect_guest_end)
                ],
                GUEST_COLLECT_END: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), collect_guest_letter_back),
                    MessageHandler(Filters.regex('^Подтвердить$'), add_guest_to_database)
                ],

                # registered branch
                REGISTERED_GAME_VIEW: [
                    MessageHandler(Filters.regex('^Информация об игре$'), registered_game_display),
                    MessageHandler(Filters.regex('^Просмотреть виш-листы других участников$'), registered_participants),
                    MessageHandler(Filters.regex('^Хочу поменять информацию о себе$'), correct_guest_data),
                    MessageHandler(Filters.regex('^Назад ⬅$'), registered_game_display)
                ],
                REGISTERED_CORRECT_DATA: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), registered_game_display),
                    MessageHandler(Filters.regex('^Исправить имя$'), correct_name),
                    MessageHandler(Filters.regex('^Исправить желание$'), correct_wishlist),
                    MessageHandler(Filters.regex('^Исправить e-mail$'), correct_email),
                    MessageHandler(Filters.regex('^Исправить письмо Санте$'), correct_letter)
                ],
                REGISTERED_CORRECT_NAME_ACCEPT: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), correct_guest_data),
                    MessageHandler(Filters.text, rewrite_name)
                ],
                REGISTERED_CORRECT_WISH_ACCEPT: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), correct_guest_data),
                    MessageHandler(Filters.text, rewrite_wishlist)
                ],
                REGISTERED_CORRECT_EMAIL_ACCEPT: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), correct_guest_data),
                    MessageHandler(Filters.regex(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), rewrite_email),
                    MessageHandler(Filters.text, correct_email)
                ],
                REGISTERED_CORRECT_LETTER_ACCEPT: [
                    MessageHandler(Filters.regex('^Назад ⬅$'), correct_guest_data),
                    MessageHandler(Filters.text, rewrite_letter)
                ],

            },
            fallbacks=[CommandHandler('start', start), MessageHandler(Filters.regex('^Начать$'), start)],
            per_user=True,
            per_chat=True,
            allow_reentry=True
        )
        dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()
