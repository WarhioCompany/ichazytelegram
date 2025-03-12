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
    def __init__(self, bot, user_id, get_button_rows_method):
        super().__init__(bot, user_id, 'challenges', parse_mode='MarkdownV2')
        self.get_button_rows = get_button_rows_method

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
            challenges = db_sess.query(Challenge).all()

            return challenges[-(self.current_page % len(challenges)) - 1]

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

    def get_winner_count(self):
        with session_scope() as session:
            return session.query(UserWork).filter(and_(
                UserWork.status == 'approved',
                UserWork.challenge_id == self.current_challenge.id
            )).count()

    def get_userworks_count(self, approved=False):
        with session_scope() as session:
            if approved:
                return session.query(UserWork).filter(and_(
                    UserWork.status == 'approved',
                    UserWork.challenge_id == self.current_challenge.id,
                    UserWork.user_id == self.user_id
                )).count()
            else:
                return session.query(UserWork).filter(and_(
                    UserWork.challenge_id == self.current_challenge.id,
                    UserWork.user_id == self.user_id
                )).count()


class ChallengePageViewerUser(ChallengePageViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, self.get_button_rows)

    def get_button_rows(self):
        return [[types.InlineKeyboardButton('Посмотреть работы', callback_data='user_works'),
                 types.InlineKeyboardButton('Участвовать', callback_data=f'participate')]]

    def submit_userwork(self, userwork, userwork_type):
        if self.current_challenge.work_type != userwork_type:
            self.bot.send_message(self.user_id, messages["incorrect_userwork_type"])
        else:
            if self.current_challenge.price != 0:
                with session_scope() as session:
                    user = session.query(User).filter(User.telegram_id == self.user_id).one()

                    print(f'{user.name}({user.coins}): {self.current_challenge.name}({self.current_challenge.price})')
                    user.coins -= self.current_challenge.price

                    session.commit()
                    print(f"{user.name}({user.coins})")

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
        return message

    def get_unused_promocodes(self):
        with session_scope() as session:
            promocodes = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().promocodes
            required_amount = sum(1 for promocode in promocodes if not promocode.is_expired)

            user_promocodes = session.query(User).filter(User.telegram_id == self.user_id).one().used_promocodes
            used_promocodes_amount = sum(1 for promocode in promocodes if promocode in user_promocodes)
            if required_amount <= used_promocodes_amount:
                return []
            return [promocode for promocode in promocodes if not (promocode.is_expired or promocode in user_promocodes)]

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
            date_uploaded=datetime.now().timestamp(),
        )
        with session_scope() as db_sess:
            db_sess.add(work)
            self.bot.send_message(self.user_id, messages["user_send_work"])
            db_sess.commit()


class ChallengePageViewerAdmin(ChallengePageViewer):
    def __init__(self, bot, admin_id, chainer):
        super().__init__(bot, admin_id, self.get_button_rows)
        self.chainer = chainer

        common_buttons = [
            types.InlineKeyboardButton('Название', callback_data='challenge_edit name'),
            types.InlineKeyboardButton('Описание', callback_data=f'challenge_edit description'),
            types.InlineKeyboardButton('Цена', callback_data=f'challenge_edit price'),
            types.InlineKeyboardButton('Лимит работ пользователя',
                                       callback_data=f'challenge_edit userwork_limit'),
            types.InlineKeyboardButton('Лимит победителей', callback_data=f'challenge_edit winner_limit'),
            types.InlineKeyboardButton('Дата окончания-', callback_data=f'challenge_edit date_to'),
            types.InlineKeyboardButton('Картинка/Видео-', callback_data=f'challenge_edit media')
        ]
        cancel_button = [types.InlineKeyboardButton('❌Отмена❌', callback_data=f'challenge_edit cancel')]

        self.buttons_easy = common_buttons + [
            types.InlineKeyboardButton('Приз лекоинами', callback_data=f'challenge_edit coins_prize')
        ] + cancel_button

        self.buttons_hard = common_buttons + [
            types.InlineKeyboardButton('Приз-', callback_data=f'challenge_edit prize'),
            types.InlineKeyboardButton('Промокоды-', callback_data=f'challenge_edit promocodes'),
            types.InlineKeyboardButton('Ссылка на пост', callback_data=f'challenge_edit post_link')
        ] + cancel_button

        self.edit_challenge_option_picker = None

    def get_button_rows(self):
        return [[types.InlineKeyboardButton('Редактировать', callback_data='challenge_edit_start'),
                 types.InlineKeyboardButton('Сделать неактивным-', callback_data=f'challenge_edit_hide')]]

    def send_edit_challenge_option_picker(self):
        buttons = self.buttons_hard if self.current_challenge.is_hard else self.buttons_easy
        markup = types.InlineKeyboardMarkup()
        [markup.add(button) for button in buttons]
        self.edit_challenge_option_picker = self.bot.send_message(self.user_id, 'Что редактируем?', reply_markup=markup).message_id

    def hide_challenge(self):
        pass

    def edit_challenge(self, option):
        self.bot.delete_message(self.user_id, self.edit_challenge_option_picker)
        if option == 'cancel':
            return

        def __edit_challenge(answer):
            answer = answer[0]
            if option in ['name', 'description', 'post_link']: # text fields
                self.edit_field(option, answer)
            elif option in ['price', 'winner_limit', 'userwork_limit', 'coins_prize']: # int fields
                self.edit_field(option, int(answer))
            self.chainer.clear_chain()

        self.chainer.chain([f'Новое {option}:'], [__edit_challenge])


    def edit_field(self, field, value):
        with session_scope() as session:
            challenge = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one()
            if field == 'name':
                challenge.name = value
            elif field == 'description':
                challenge.description = value
            elif field == 'price':
                challenge.price = value
            elif field == 'userwork_limit':
                challenge.userworks = value
            elif field == 'winner_limit':
                challenge.winner_limit = value
            elif field == 'date_to':
                challenge.date_to = value
            elif field == 'media':
                if challenge.video:
                    challenge.video = value
                else:
                    challenge.image = value
            elif field == 'coins_prize':
                challenge.coins_prize = value
            elif field == 'post_link':
                challenge.post_link = value
            session.commit()
        self.current_challenge = self.get_challenge()
        self.update_page(self.get_media(), self.get_button_rows())

# name, desc, image/video, price, date_to, userwork_limit, winner_limit, coins_prize
