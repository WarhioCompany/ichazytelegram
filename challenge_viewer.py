from datetime import datetime

from db_scripts.db import get_challenge_by_id
from challenge import Challenge
from telebot import types
from messages_handler import messages


class ChallengeViewer:
    def __init__(self):
        self.current_page = 0
        self.challenges_on_page = 3

    def get_challenges_objects(self):
        return [challenge for challenge in (Challenge(i + 1) for i in range(self.challenges_on_page)) if challenge.name]

    def get_media_group(self, challenges):
        media = [types.InputMediaPhoto(challenge.image) for challenge in challenges]
        media[0].caption = '\n'.join(messages['challenge_page_challenge_element'].format(
            id=i,
            name=challenges[i].name,
            desc=challenges[i].desc,
            price=challenges[i].price,
            coins=challenges[i].coins_prize,
            date_to=datetime.strftime(challenges[i].date_to, '%d/%m/%y')
        ) for i in range(len(challenges)))
        return media

    def get_buttons(self, length):
        markup = types.InlineKeyboardMarkup()

        markup.add(*[types.InlineKeyboardButton(f'{i + 1}', callback_data=f'{i + 1}') for i in range(length)])
        return markup
