from datetime import datetime

from docutils.nodes import description
from sqlalchemy import and_, not_
from telebot import types

import logger.bot_logger
from db_data.db_session import session_scope
#from db_tweaks.change_db import challenge
from messages_handler import messages

from db_data.models import Challenge, UserWork, Prize, Promocode, User
from db_data import db_session, db_tools
from page_viewer.page_viewer import PageViewer


class ChallengePageViewer(PageViewer):
    def __init__(self, bot, user_id, get_button_rows_method, only_active, menu_button):
        super().__init__(bot, user_id, 'challenges', parse_mode='MarkdownV2', menu_button=menu_button)
        self.get_button_rows = get_button_rows_method
        self.only_active = only_active

        self.current_challenge = None

    def show_challenges(self):
        self.reset()
        self.current_challenge = self.get_challenge()

        if self.current_challenge:
            self.send_page(self.get_media(), self.get_button_rows())
        else:
            self.send_empty_page()

    def send_empty_page(self):
        self.send_message('Нет челленджей', reply_markup=self.get_markup(self.get_button_rows(True)))

    def challenge_refresh(self):
        self.current_challenge = self.get_challenge()
        self.update_page(self.get_media(), self.get_button_rows())

    def next_page(self):
        self.current_page += 1
        self.challenge_refresh()

    def prev_page(self):
        self.current_page -= 1
        self.challenge_refresh()

        if self.current_page == -1:
            with session_scope() as db_sess:
                self.current_page = db_sess.query(Challenge).count() - 1

    def get_challenge(self):
        with session_scope() as db_sess:
            if self.only_active:
                challenges = db_sess.query(Challenge).filter(not_(Challenge.is_hidden)).all()
            else:
                challenges = db_sess.query(Challenge).all()

            if not challenges: return None
            return challenges[-(self.current_page % len(challenges)) - 1]

    def get_media(self):
        if self.current_challenge.preview_type == 'image':
            media = types.InputMediaPhoto(self.current_challenge.preview)
        elif self.current_challenge.preview_type == 'video':
            media = types.InputMediaVideo(self.current_challenge.preview)
        else:
            raise Exception(f'Unknown preview type: {self.current_challenge.preview_type}')

        text = self.challenge_page_text()
        media.caption = text
        return media

    def challenge_page_text(self):
        with session_scope() as session:
            prizes = session.query(Challenge).filter(
                Challenge.id == self.current_challenge.id
            ).one().prizes
            prize_name = None
            if prizes:
                prize_name = prizes[0].name

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
            prize_name=prize_name,
            promocodes=self.promocode_text(),
            link=self.current_challenge.post_link,
            winner_count=self.get_winner_count(),
            userworks_approved=self.get_userworks_count(approved=True)
        )

    def promocode_text(self):
        with session_scope() as session:
            challenge = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one()
            promocodes = [promocode for promocode in challenge.promocodes if not promocode.is_expired]

            user = session.query(User).filter(User.telegram_id == self.user_id).all()
            promocodes_used = []
            if user:
                promocodes_used = user[0].used_promocodes

            text_promo = []

            for promocode in promocodes:
                if promocode in promocodes_used:
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
    def __init__(self, bot, user):
        super().__init__(bot, user.user_id, self.get_button_rows, True, True)

    def get_button_rows(self, empty_page_buttons=False):
        if empty_page_buttons: return []

        userworks_button = types.InlineKeyboardButton('Посмотреть работы', callback_data='user_works')
        participate_button = types.InlineKeyboardButton('Участвовать', callback_data=f'participate')

        if self.current_challenge.is_hard:
            prize_button = types.InlineKeyboardButton('Что за приз?', callback_data=f'view_prize {self.get_prize_id()}')
            return [[userworks_button, prize_button], [participate_button]]
        else:
            return [[userworks_button, participate_button]]

    def get_prize_id(self):
        with session_scope() as session:
            prizes = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().prizes
            if prizes:
                return prizes[0].id
            return -1

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
                prize = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one().prizes[0]
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

    def enough_coins(self): # BUG: Данные о стоимости могут быть не обновлены, то есть юзер тыкает на кнопку "участвовать", но данные о стоимости не обновляются
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


# allows admin to edit a challenge (challenge_edit callback) or create one (challenge_create callback)
class ChallengePageViewerAdmin(ChallengePageViewer):
    def __init__(self, bot, admin_id, chainer):
        super().__init__(bot, admin_id, self.get_button_rows, False, False)
        self.chainer = chainer

        common_buttons = [
            types.InlineKeyboardButton('Название', callback_data='challenge_edit name'),
            types.InlineKeyboardButton('Описание', callback_data=f'challenge_edit description'),
            types.InlineKeyboardButton('Цена', callback_data=f'challenge_edit price'),
            types.InlineKeyboardButton('Лимит работ пользователя',
                                       callback_data=f'challenge_edit userwork_limit'),
            types.InlineKeyboardButton('Лимит победителей', callback_data=f'challenge_edit winner_limit'),
            types.InlineKeyboardButton('Дата окончания-', callback_data=f'challenge_edit date_to'),
            types.InlineKeyboardButton('Картинка/Видео', callback_data=f'challenge_edit preview')
        ]
        cancel_button = [types.InlineKeyboardButton('❌Отмена❌', callback_data=f'challenge_edit cancel')]

        self.buttons_easy = common_buttons + [
            types.InlineKeyboardButton('Приз лекоинами', callback_data=f'challenge_edit coins_prize')
        ] + cancel_button

        self.buttons_hard = common_buttons + [
            types.InlineKeyboardButton('Приз', callback_data=f'challenge_edit prize'),
            types.InlineKeyboardButton('Промокоды-', callback_data=f'challenge_edit promocodes'),
            types.InlineKeyboardButton('Ссылка на пост', callback_data=f'challenge_edit post_link')
        ] + cancel_button

        self.edit_challenge_option_picker = None

        self.easy_challenge_args, self.hard_challenge_args = self.get_challenge_args()


    def handle_edit_challenge_callback(self, call):
        if call.data == 'challenge_edit_start':
            self.send_edit_challenge_option_picker()
        else:
            option = call.data.split()[1]
            if option == 'hidden':
                self.change_is_hidden_field()
            else:
                self.edit_challenge(option)

    def get_activity_button_text(self):
        return 'Сделать активным' if self.current_challenge.is_hidden else 'Скрыть'


    def get_button_rows(self, is_empty_page_buttons=False):
        create_button = types.InlineKeyboardButton('Создать челлендж', callback_data='challenge_create_start')
        if is_empty_page_buttons: return [[create_button]]
        activity_button_text = self.get_activity_button_text()

        return [[types.InlineKeyboardButton('Редактировать', callback_data='challenge_edit_start'), types.InlineKeyboardButton(activity_button_text, callback_data='challenge_edit hidden')],
                [create_button]]

    def send_edit_challenge_option_picker(self):
        self.chainer.clear_chain()
        buttons = self.buttons_hard if self.current_challenge.is_hard else self.buttons_easy
        markup = types.InlineKeyboardMarkup()
        [markup.add(button) for button in buttons]
        self.edit_challenge_option_picker = self.bot.send_message(self.user_id, 'Что редактируем?', reply_markup=markup).message_id


    def change_is_hidden_field(self):
        with session_scope() as session:
            challenge = session.query(Challenge).filter(Challenge.id == self.current_challenge.id).one()
            challenge.is_hidden = not challenge.is_hidden
            session.commit()
        self.challenge_refresh()

    def edit_challenge(self, option):
        self.bot.delete_message(self.user_id, self.edit_challenge_option_picker)
        if option == 'cancel':
            return

        def __edit_challenge(answer):
            answer = answer[0]
            if option in ['name', 'description', 'post_link', 'preview', 'prize']: # text fields + media
                self.edit_field(option, answer)
            elif option in ['price', 'winner_limit', 'userwork_limit', 'coins_prize']: # int fields
                print(answer)
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
                challenge.userwork_limit = value
            elif field == 'winner_limit':
                challenge.winner_limit = value
            elif field == 'date_to':
                challenge.date_to = value
            elif field == 'preview':
                if isinstance(value, types.InputMediaPhoto):
                    challenge.preview = value.media
                    challenge.preview_type = 'image'
                else: # InputMediaVideo
                    challenge.preview = value.media
                    challenge.preview_type = 'video'
            elif field == 'coins_prize':
                challenge.coins_prize = value
            elif field == 'post_link':
                challenge.post_link = value
            elif field == 'prize':
                prize = self.get_prize_from_answer(session, value)
                if prize:
                    challenge.prizes = [prize]


            session.commit()
        self.challenge_refresh()


    def get_prize_from_answer(self, session, value):
        if value.isdigit():
            prize = session.query(Prize).filter(Prize.id == int(value)).all()
        else:
            prize = session.query(Prize).filter(Prize.name == value).all()

        if len(prize) == 0:
            self.bot.send_message(self.user_id, 'Такой приз не найден')
        else:
            return prize[0]



    def get_challenge_args(self):
        args = {'description': 'описание',
                'is_hidden': True,
                'preview': db_tools.get_empty_image(),
                'preview_type': 'image',
                'price': 100,
                'date_to': datetime.now(),
                'work_type': 'image',
                'userwork_limit': 100,
                'winner_limit': 100
        }
        easy_challenge_args = {
            'name': '#easychallenge',
            'is_hard': False,
            'coins_prize': 1000
        } | args
        hard_challenge_args = {
            'name': '#hardchallenge',
            'is_hard': True,
            'prizes': [],
            'post_link': 'www.google.com',
        } | args
        return easy_challenge_args, hard_challenge_args



    def send_challenge_is_hard_picker(self):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Простой', callback_data='challenge_create easy'),
                   types.InlineKeyboardButton('Сложный', callback_data='challenge_create hard'))

        self.edit_challenge_option_picker = self.bot.send_message(self.user_id, 'Тип челленджа', reply_markup=markup).message_id


    def create_challenge(self, challenge_args):
        with session_scope() as session:
            session.add(Challenge(**challenge_args))
            session.commit()
        self.current_page = 0
        self.challenge_refresh()


    def handle_create_challenge_callback(self, call):
        if call.data == 'challenge_create_start':
            self.send_challenge_is_hard_picker()
        else:
            self.bot.delete_message(self.user_id, self.edit_challenge_option_picker)
            option = call.data.split()[1]
            if option == 'easy':
                self.create_challenge(self.easy_challenge_args)
            elif option == 'hard':
                self.create_challenge(self.hard_challenge_args)
