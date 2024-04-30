from datetime import datetime

from user_work import UserWork
from challenge_card import ChallengeCard
from db_scripts.db import get_user_works_amount, get_user_works_ids_by_challenge_id, get_user_username
from telebot import types
from messages_handler import messages


class UserWorksPageViewer:
    def __init__(self, bot, user_id):
        self.current_page = 0
        self.works_on_page = 3
        self.current_works = []
        self.current_works_ids = []
        self.images_ids = []
        self.picker_id = None
        # self.challenge_card = ChallengeCard(bot, user_id)

        self.bot = bot
        self.user_id = user_id
        self.challenge_id = None

    def reset(self):
        self.current_page = 0

    def show_works(self, challenge_id):
        self.current_works_ids = get_user_works_ids_by_challenge_id(challenge_id)

        picker_to_delete = self.picker_id
        page_to_delete = self.images_ids
        # challenge_card = self.challenge_card
        self.reset()

        self.get_user_works()
        if self.current_works:
            media = self.get_media_group()

            messages_data = self.bot.send_media_group(self.user_id, media=media)
            self.images_ids = [message.message_id for message in messages_data]

            self.picker_id = self.bot.send_message(self.user_id, messages["userworks_picker"],
                                                   reply_markup=self.get_buttons([
                                                       work.like_count for work in self.current_works
                                                   ])).id
        else:
            self.picker_id = self.bot.send_message(self.user_id, messages['no_userworks_found']).id
            self.images_ids = []

        self.delete_if_exists(page_to_delete, picker_to_delete)     # , challenge_card)

    # def send_challenge(self, challenge_id):
    #    self.challenge_card.show_info(self.current_works[challenge_id])

    def delete_if_exists(self, page, picker):  # , card):
        if picker:
            self.bot.delete_message(self.user_id, picker)
            for message in page:
                self.bot.delete_message(self.user_id, message)
            # card.delete()

    def update_message(self):
        self.get_user_works()
        media = self.get_media_group()

        for i in range(self.works_on_page):
            self.bot.edit_message_media(chat_id=self.user_id, message_id=self.images_ids[i], media=media[i])

    def get_user_works(self):
        self.current_works.clear()

        if self.current_works_ids:
            for i in range(self.works_on_page):
                work_id = (self.current_page * self.works_on_page + i) % len(self.current_works_ids)
                self.current_works.append(UserWork(work_id=self.current_works_ids[work_id]['id']))
        else:
            self.current_works = []

    def get_media_group(self):
        media = []
        for work in self.current_works:
            if work.type == 'video':
                media.append(types.InputMediaVideo(work.data))
            else:
                media.append(types.InputMediaPhoto(work.data))
        media[0].caption = self.works_page_text()
        return media

    def next_page(self):
        self.current_page += 1
        self.update_message()

    def prev_page(self):
        if self.current_page != 0:
            self.current_page -= 1
            self.update_message()

    def works_page_text(self):
        return '\n'.join(messages['user_work_page_work_element'].format(
            id=i + 1,
            username=get_user_username(self.current_works[i].user_id),
        ) for i in range(len(self.current_works)))

    def like_userwork(self, work_id):
        self.current_works[work_id].like_count += 1
        self.current_works[work_id].update_db()

    def get_buttons(self, likes):
        markup = types.InlineKeyboardMarkup()

        markup.add(*[types.InlineKeyboardButton(f'{i + 1}: {likes[i]}❤', callback_data=f'userwork_like {i}')
                     for i in range(len(self.current_works))])
        markup.add(types.InlineKeyboardButton('⬅', callback_data='prev_page_userworks'),
                   types.InlineKeyboardButton('➡', callback_data='next_page_userworks'))
        return markup