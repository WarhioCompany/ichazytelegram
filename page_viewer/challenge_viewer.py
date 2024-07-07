from datetime import datetime

from sqlalchemy import and_

from page_viewer.challenge_card import ChallengeCard
from telebot import types

from db_data.db_session import session_scope
from messages_handler import messages

from db_data.models import Challenge, UserWork
from db_data import db_session
from page_viewer.page_viewer import PageViewer


class ChallengePageViewer(PageViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id)

        self.challenges_on_page = 3
        self.current_challenges = []

        self.challenge_card = ChallengeCard(bot, user_id)

    def show_challenges(self):
        self.current_challenges = self.get_challenges()
        self.challenge_card.delete()
        self.send_page(self.get_media_group())
        self.send_picker(messages["challenge_picker"], self.get_buttons())

    def next_page(self):
        self.current_page += 1
        self.current_challenges = self.get_challenges()
        self.update_page(self.get_media_group())

    def prev_page(self):
        if self.current_page != 0:
            self.current_page -= 1
            self.current_challenges = self.get_challenges()
            self.update_page(self.get_media_group())

    def send_challenge(self, challenge_id):
        self.challenge_card.show_info(self.current_challenges[challenge_id])

    def get_challenges(self):
        res = []
        with session_scope() as db_sess:
            challenges_amount = db_sess.query(Challenge).count()

            for i in range(self.challenges_on_page):
                challenge_id = (self.current_page * self.challenges_on_page + i) % challenges_amount + 1
                res.append(db_sess.query(Challenge).filter(Challenge.id == challenge_id).first())
        return res

    def get_media_group(self):
        media = [types.InputMediaPhoto(challenge.image) for challenge in self.current_challenges]
        media[0].caption = self.challenge_page_text()
        return media

    def challenge_page_text(self):
        return '\n'.join(messages['challenge_page_challenge_element'].format(
            id=i + 1,
            name=self.current_challenges[i].name,
            desc=self.current_challenges[i].description,
            price=self.current_challenges[i].price,
            coins=self.current_challenges[i].coins_prize,
            date_to=datetime.strftime(self.current_challenges[i].date_to, '%d/%m/%y')
        ) for i in range(len(self.current_challenges)))

    def get_buttons(self):
        markup = types.InlineKeyboardMarkup()

        markup.add(*[types.InlineKeyboardButton(f'{i + 1}', callback_data=f'challenge_card {i}')
                     for i in range(len(self.current_challenges))])
        markup.add(types.InlineKeyboardButton('⬅', callback_data='prev_page challenges'),
                   types.InlineKeyboardButton('➡', callback_data='next_page challenges'))
        return markup

    def submit_userwork(self, userwork, userwork_type):
        if self.challenge_card.current_challenge.work_type != userwork_type:
            self.bot.send_message(self.user_id, messages["incorrect_userwork_type"])
        else:
            self.upload_work(userwork, userwork_type)

    def is_limit_exceeded(self):
        challenge = self.challenge_card.current_challenge
        with session_scope() as session:
            userworks_count = session.query(UserWork).filter(and_(UserWork.user_id == self.user_id,
                                                                  UserWork.challenge_id == challenge.id)).count()
        if userworks_count >= challenge.userwork_limit:
            return True
        return False

    def upload_work(self, userwork, userwork_type):
        work = UserWork(
            user_id=self.user_id,
            challenge_id=self.challenge_card.current_challenge.id,
            data=userwork,
            type=userwork_type,
            date_uploaded=datetime.now(),
        )
        with session_scope() as db_sess:
            db_sess.add(work)
            self.bot.send_message(self.user_id, messages["user_send_work"])
            db_sess.commit()
