from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import json
from telegram.utils import helpers


ADMIN_GAME_VIEW, ADMIN_PARTICIPANTS = range(10, 12)
GUEST_COLLECT_PD, GUEST_COLLECT_WISH = range(20, 22)


def start_santa_game(update, context):
    game_name = context.args[0]
    context.user_data['game_name'] = game_name
    user = update.message.from_user
    first_name = user.first_name

    with open(file=f'{game_name}.json', mode='r') as file:
        text = json.load(file)
        game_owner = text['game_owner']

    if first_name == game_owner:
        keyboard = [
            ['Информация об игре'],
            ['Список участников'],
            ['Ввести данные для участия в игре']
        ]
        update.message.reply_text(
            f'Похоже, что Вы - создатель игры: {game_name}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        return ADMIN_GAME_VIEW

    else:
        keyboard = [
            ['Рассказать Санте о себе']
        ]
        update.message.reply_text(
            f'Привет! {game_owner} приглашает тебя поучаствовать в игре {game_name}:\n'
            f'Расскажи Санте о себе, как тебя зовут и что бы ты хотел получить на Новый Год',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

        return GUEST_COLLECT_PD


def collect_guest_name(update, context):
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.first_name
    keyboard = [
        ['Ввести полное ФИО'],
        ['Подтвердить']
    ]
    update.message.reply_text(
        f'Фамилия и имя, взятые из твоего профиля'
        f'{first_name}'
        f'{last_name}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )
    return GUEST_COLLECT_WISH


def collect_guest_wish(update, context):
    user = update.message.from_user

    if update.message.text != 'Назад ⬅':
        first_name = user.first_name
        last_name = user.first_name
        game_name = context.user_data['game_name']
        with open(file=f'{game_name}.json', mode='a') as file:
            file.write(f'В игре: {first_name}, {last_name}')


def collect_guest_name_back(update, context):
    return collect_guest_name(update, context)


def admin_participants(update, context):
    bot = context.bot
    game_name = context.user_data['game_name']
    with open(file=f'{game_name}.json', mode='r') as file:
        url = helpers.create_deep_linked_url(bot.username, game_name)
        text = json.load(file)
        game_participants = text.get("game_participants")
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


