from datetime import datetime

from challenge import Challenge
from challenge_card import ChallengeCard
from db_scripts.db import get_challenges_amount
from telebot import types
from messages_handler import messages


class ChallengePageViewer:
    def __init__(self, bot, user_id):
        self.current_page = 0
        self.challenges_on_page = 6
        self.current_challenges = []
        self.images_ids = []
        self.picker_id = None
        self.challenge_card = ChallengeCard(bot, user_id)

        self.bot = bot
        self.user_id = user_id

    def reset(self):
        self.current_page = 0

    def show_challenges(self):
        picker_to_delete = self.picker_id
        page_to_delete = self.images_ids
        challenge_card = self.challenge_card
        self.reset()

        self.get_challenges()
        media = self.get_media_group()

        messages_data = self.bot.send_media_group(self.user_id, media=media)
        self.images_ids = [message.message_id for message in messages_data]

        self.picker_id = self.bot.send_message(self.user_id, messages["challenge_picker"],
                                               reply_markup=self.get_buttons()).id

        self.delete_if_exists(picker_to_delete, page_to_delete, challenge_card)

    def send_challenge(self, challenge_id):
        self.challenge_card.show_info(self.current_challenges[challenge_id])

    def delete_if_exists(self, picker, page, card):
        if page:
            for message in page + [picker]:
                self.bot.delete_message(self.user_id, message)
            card.delete()

    def update_message(self):
        self.get_challenges()
        media = self.get_media_group()

        for i in range(self.challenges_on_page):
            self.bot.edit_message_media(chat_id=self.user_id, message_id=self.images_ids[i], media=media[i])

    def get_challenges(self):
        self.current_challenges.clear()
        challenges_amount = get_challenges_amount()

        for i in range(self.challenges_on_page):
            challenge_id = (self.current_page * self.challenges_on_page + i) % challenges_amount + 1
            self.current_challenges.append(Challenge(challenge_id))

    def get_media_group(self):
        media = [types.InputMediaPhoto(challenge.image) for challenge in self.current_challenges]
        media[0].caption = self.challenge_page_text()
        return media

    def next_page(self):
        self.current_page += 1
        self.update_message()

    def prev_page(self):
        if self.current_page != 0:
            self.current_page -= 1
            self.update_message()

    def challenge_page_text(self):
        return '\n'.join(messages['challenge_page_challenge_element'].format(
            id=i + 1,
            name=self.current_challenges[i].name,
            desc=self.current_challenges[i].desc,
            price=self.current_challenges[i].price,
            coins=self.current_challenges[i].coins_prize,
            date_to=datetime.strftime(self.current_challenges[i].date_to, '%d/%m/%y')
        ) for i in range(len(self.current_challenges)))

    def get_buttons(self):
        markup = types.InlineKeyboardMarkup()

        markup.add(*[types.InlineKeyboardButton(f'{i + 1}', callback_data=f'challenge_card {i}')
                     for i in range(len(self.current_challenges))])
        markup.add(types.InlineKeyboardButton('⬅', callback_data='prev_page_challenges'),
                   types.InlineKeyboardButton('➡', callback_data='next_page_challenges'))
        return markup