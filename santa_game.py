from telegram import ReplyKeyboardMarkup


def start_santa_game(update, context):
    game_name = context.args[0]
    user = update.message.from_user
    first_name = user.first_name

    with open(file=f"{game_name}.txt", mode="r") as file:
        text = file.read()
        game_owner = text.split("owner")[1].strip()

    if first_name == game_owner:
        keyboard = [
            ["Информация об игре"],
            ["Список участников"],
            ["Ввести данные для участия в игре"]
        ]
        update.message.reply_text(
            f'Похоже, что Вы - создатель игры: {game_name}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        # fix this state
        return None

    else:
        keyboard = [
            ["Рассказать Санте о себе"]
        ]
        update.message.reply_text(
            f'Привет! {game_owner} приглашает тебя поучаствовать в игре {game_name}:'
            f'Расскажи Санте о себе, как тебя зовут и что бы ты хотел получить на Новый Год',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        # fix this state
        return None