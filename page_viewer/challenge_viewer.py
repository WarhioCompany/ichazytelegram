from datetime import datetime

from sqlalchemy import and_

from page_viewer.challenge_card import ChallengeCard
from telebot import types

from db_data.db_session import session_scope
from messages_handler import messages

from db_data.models import Challenge, UserWork, Prize, Promocode, User
from db_data import db_session
from page_viewer.page_viewer import PageViewer


class ChallengePageViewer(PageViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'challenges', parse_mode='MarkdownV2')

        self.current_challenge = None

    def show_challenges(self):
        self.reset()
        self.current_challenge = self.get_challenge()

        self.send_page(self.get_media(), self.get_button_rows())

    def next_page(self):
        self.current_page += 1
        self.current_challenge = self.get_challenge()
        self.update_page(self.get_media(), self.get_button_rows())

    def prev_page(self):
        self.current_page -= 1
        self.current_challenge = self.get_challenge()
        self.update_page(self.get_media(), self.get_button_rows())

        if self.current_page == -1:
            with session_scope() as db_sess:
                self.current_page = db_sess.query(Challenge).count() - 1

    def get_challenge(self):
        with session_scope() as db_sess:
            challenges_amount = db_sess.query(Challenge).count()

            challenge_id = self.current_page % challenges_amount + 1
            return db_sess.query(Challenge).filter(Challenge.id == challenge_id).first()

    def get_media(self):
        if self.current_challenge.image:
            media = types.InputMediaPhoto(self.current_challenge.image)
        else:
            media = types.InputMediaVideo(self.current_challenge.video)
        text = self.challenge_page_text()
        media.caption = text
        return media

    def challenge_page_text(self):
        with session_scope() as session:
            prize = session.query(Challenge).filter(
                Challenge.id == self.current_challenge.id
            ).one().prize
            prize_desc = None
            if prize:
                prize_desc = prize.description

        if self.current_challenge.is_hard:
            message = messages["challenge_page_element_prize"]
        else:
            message = messages['challenge_page_element_coins']

        return message.format(
            name=self.current_challenge.name,
            desc=self.current_challenge.description,
            price=self.current_challenge.price,
            date_to=datetime.strftime(self.current_challenge.date_to, '%d/%m/%y'),
            work_type=self.current_challenge.work_type,
            userwork_limit=self.current_challenge.userwork_limit,
            winner_limit=self.current_challenge.winner_limit,
            coins_prize=self.current_challenge.coins_prize,
            prize_desc=prize_desc,
            promocodes=self.promocode_text(),
            link=self.current_challenge.post_link,
            winner_count=self.get_winner_count(),
            userworks_approved=self.get_userworks_count(approved=True)
        )

    def promocode_text(self):
        with session_scope() as session:
            challenge = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one()
            user = session.query(User).filter(User.telegram_id == self.user_id).one()
            promocodes = [promocode for promocode in challenge.promocodes if not promocode.is_expired]

            text_promo = []

            for promocode in promocodes:
                if promocode in user.used_promocodes:
                    text_promo.append(f"~{promocode.promo}~")
                else:
                    text_promo.append(f"{promocode.promo}")

            return "\n".join(text_promo)

    def get_button_rows(self):
        return [[types.InlineKeyboardButton('Посмотреть работы', callback_data='user_works'),
                 types.InlineKeyboardButton('Участвовать', callback_data=f'participate')]]

    def submit_userwork(self, userwork, userwork_type):
        if self.current_challenge.work_type != userwork_type:
            self.bot.send_message(self.user_id, messages["incorrect_userwork_type"])
        else:
            with session_scope() as session:
                user = session.query(User).filter(User.telegram_id == self.user_id).one()
                print(f'CHALLENGE NAME: {self.current_challenge.name}\nPRICE: {self.current_challenge.price}\nUSER BALANCE: {user.coins}')
                user.coins -= self.current_challenge.price
                session.commit()
                print(f"CURRENT BALANCE: {user.coins}")
            self.upload_work(userwork, userwork_type)

    def can_submit(self):
        userworks_count = self.get_userworks_count()
        winner_count = self.get_winner_count()

        unused_promocodes = self.get_unused_promocodes()
        if userworks_count >= self.current_challenge.userwork_limit:
            message = messages["userwork_limit_exceeded"]
        elif winner_count >= self.current_challenge.winner_limit:
            message = messages["winner_limit_exceeded"]
        elif unused_promocodes:
            promocodes_text = '\n'.join(promocode.promo for promocode in unused_promocodes)
            with session_scope() as session:
                prize = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().prize
            message = messages['insufficient_challenge_condition'].format(
                promocodes=promocodes_text,
                link=self.current_challenge.post_link,
                prize_desc=prize.description
            )
        elif not self.enough_coins():
            with session_scope() as session:
                price = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().price
            message = messages["not_enough_coins"].format(price=price)
        else:
            return ''
        return self.escape(message)

    def get_unused_promocodes(self):
        with session_scope() as session:
            promocodes = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().promocodes
            required_amount = sum(1 for promocode in promocodes if not promocode.is_expired)

            user_promocodes = session.query(User).filter(User.telegram_id == self.user_id).one().used_promocodes
            used_promocodes_amount = sum(1 for promocode in promocodes if promocode in user_promocodes)
            if required_amount <= used_promocodes_amount:
                return []
            return [promocode for promocode in promocodes if not (promocode.is_expired or promocode in user_promocodes)]

    def get_winner_count(self):
        with session_scope() as session:
            return session.query(UserWork).filter(and_(
                UserWork.is_approved,
                UserWork.challenge_id == self.current_challenge.id
            )).count()

    def get_userworks_count(self, approved=False):
        with session_scope() as session:
            if approved:
                return session.query(UserWork).filter(and_(
                    UserWork.is_approved,
                    UserWork.challenge_id == self.current_challenge.id,
                    UserWork.user_id == self.user_id
                )).count()
            else:
                return session.query(UserWork).filter(and_(
                    UserWork.challenge_id == self.current_challenge.id,
                    UserWork.user_id == self.user_id
                )).count()

    def enough_coins(self):
        with session_scope() as session:
            user_coins = session.query(User).filter(User.telegram_id == self.user_id).one().coins
            return user_coins >= self.current_challenge.price

    def upload_work(self, userwork, userwork_type):
        work = UserWork(
            user_id=self.user_id,
            challenge_id=self.current_challenge.id,
            data=userwork,
            type=userwork_type,
            date_uploaded=datetime.now(),
        )
        with session_scope() as db_sess:
            db_sess.add(work)
            self.bot.send_message(self.user_id, messages["user_send_work"])
            db_sess.commit()
