from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import json
from telegram.utils import helpers


ADMIN_GAME_VIEW, ADMIN_PARTICIPANTS = range(10, 12)
GUEST_COLLECT_NAME, GUEST_COLLECT_WISH, GUEST_COLLECT_MAIL, GUEST_COLLECT_LETTER, GUEST_COLLECT_END = range(20, 25)


def start_santa_game(update, context):

    game_name = context.args[0]
    context.user_data['game_name'] = game_name
    context.user_data['user_id'] = update.message.from_user.id
    user_id = context.user_data['user_id']

    with open(file=f'{game_name}.json', mode='r') as file:
        game = json.load(file)
        game_owner = game['game_owner']

    if user_id == game_owner:
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
            ['Ура! Сейчас я расскажу, что хочу получить на Новый Год!']
        ]

        with open(file=f'{game_name}.json', mode='r') as file:
            game = json.load(file)
            game_details = game["game_details"]

        update.message.reply_text(
            f'Привет! {game_owner} приглашает тебя поучаствовать в игре Тайный Санта!\n'
            f'Название игры: {game_name}\n'
            f'Подарки должны стоить: {game_details["game_price"]}\n'
            f'Последний день для регистрации: {game_details["game_reg_ends"]}\n'
            f'А подарочки отправим вот когда: {game_details["game_gift_date"]}\n',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

        return GUEST_COLLECT_NAME


def collect_guest_name(update, context):
    user = update.message.from_user
    first_name = user.first_name
    keyboard = [
        ['Ввести полное ФИО (в разаработке)'],
        ['Подтвердить'],
        ['Назад ⬅']
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
    return GUEST_COLLECT_WISH


def collect_guest_name_back(update, context):
    return collect_guest_name(update, context)


def collect_guest_wish(update, context):
    user = update.message.from_user

    keyboard = [
        ['Назад ⬅']
    ]

    if update.message.text != 'Назад ⬅':
        first_name = user.first_name
        game_name = context.user_data['game_name']

        with open(file=f'{game_name}.json', mode='r') as file:
            game = json.load(file)

            game["game_participants"].update(
                {first_name: {"pair": None, "wish": None, "mail": None, "letter": None}}
            )

        with open(file=f'{game_name}.json', mode='w') as file:
            json.dump(game, file, ensure_ascii=False)


    update.message.reply_text(
        f'Теперь твое желание!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

    return GUEST_COLLECT_MAIL


def collect_guest_wish_back(update, context):
    return collect_guest_wish(update, context)


def collect_guest_mail(update, context):
    user = update.message.from_user
    first_name = user.first_name
    game_name = context.user_data['game_name']

    keyboard = [['Назад ⬅']]

    if update.message.text != 'Назад ⬅':

        wish = update.message.text

        with open(file=f'{game_name}.json', mode='r') as file:
            game = json.load(file)
            game["game_participants"][first_name]["wish"] = wish

        with open(file=f'{game_name}.json', mode='w') as file:
            json.dump(game, file, ensure_ascii=False)

    update.message.reply_text(
        f'Введи, пожалуйста, свою электронную почту!',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True)
    )

    return GUEST_COLLECT_LETTER


def collect_guest_mail_back(update, context):
    return collect_guest_mail(update, context)


def collect_guest_letter(update, context):
    user = update.message.from_user
    first_name = user.first_name
    game_name = context.user_data['game_name']
    keyboard = [['Назад ⬅']]

    if update.message.text != 'Назад ⬅':

        mail = update.message.text

        with open(file=f'{game_name}.json', mode='r') as file:
            game = json.load(file)
            game["game_participants"][first_name]["mail"] = mail

        with open(file=f'{game_name}.json', mode='w') as file:
            json.dump(game, file, ensure_ascii=False)

    update.message.reply_text(
        f'Как насчет коротенького послания Санте?',
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True)
    )

    return GUEST_COLLECT_END


def collect_guest_letter_back(update, context):
    return collect_guest_letter(update, context)


def collect_guest_end(update, context):
    user = update.message.from_user
    first_name = user.first_name
    game_name = context.user_data['game_name']

    if update.message.text != 'Назад ⬅':

        letter = update.message.text

        with open(file=f'{game_name}.json', mode='r') as file:
            game = json.load(file)
            game["game_participants"][first_name]["letter"] = letter

        with open(file=f'{game_name}.json', mode='w') as file:
            json.dump(game, file, ensure_ascii=False)

    update.message.reply_text(
        f'Поздравляю! Ты в игре. В назначенный день жди своего письма!',
        reply_markup=ReplyKeyboardRemove()
    )

    return GUEST_COLLECT_END


def admin_participants(update, context):
    bot = context.bot
    game_name = context.user_data['game_name']
    url = helpers.create_deep_linked_url(bot.username, game_name)

    with open(file=f'{game_name}.json', mode='r') as file:
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

