from db_data.db_session import session_scope
from db_data.models import User, UserWork
from telebot import types
from messages_handler import messages
from sqlalchemy import and_, not_
from admin_bot import hard_userworks_messager

from page_viewer.page_viewer import PageViewer


class UserWorksViewer(PageViewer):
    def __init__(self, bot, user_id, page_type, get_userwork_func, messages_handler, get_button_rows):
        super().__init__(bot, user_id, page_type)

        self.current_work = None

        self.get_userwork_func = get_userwork_func
        self.messages_handler = messages_handler
        self.get_button_rows = get_button_rows

        # self._session = None
        self.pages_amount = -1

    def show_works(self, *args):
        self.reset()
        # self._session = create_session()

        self.current_work = self.get_userwork_func()
        if self.current_work:
            self.send_page(self.get_media(), self.get_button_rows())
        else:
            self.send_message(self.messages_handler('nothing_found'))

    def get_media(self):
        if self.current_work.type == 'video':
            media = types.InputMediaVideo(self.current_work.data)
        else:   # image
            media = types.InputMediaPhoto(self.current_work.data)
        media.caption = self.works_page_text()
        return media

    def next_page(self):
        self.current_page += 1
        self.update()

    def prev_page(self):
        if self.current_page != 0:
            self.current_page -= 1
            self.update()

    def update(self):
        self.current_work = self.get_userwork_func()

        if self.current_work:
            self.update_page(self.get_media(), self.get_button_rows())
        else:
            self.reset()
            self.send_message(self.messages_handler('nothing_found'))

    def works_page_text(self):
        with session_scope() as session:
            current_work = session.query(UserWork).filter(UserWork.id == self.current_work.id).one()
            return self.messages_handler('page_text').format(
                username=current_work.user.name,
                challenge=current_work.challenge.name,
                current_page=self.current_page % self.pages_amount + 1,
                pages_amount=self.pages_amount
            )

    def does_exist(self):
        return bool(self.current_work)

    def get_like_buttons(self):
        buttons = []
        user_dummy = User(telegram_id=f'{self.user_id}')
        # ❤ 🤍
        with session_scope() as session:
            users_liked = session.query(UserWork).filter(UserWork.id == self.current_work.id).one().users_liked
            if user_dummy in users_liked:
                s = f'{len(users_liked)}❤'
            else:
                s = f'{len(users_liked)}🤍'
        buttons.append(types.InlineKeyboardButton(s, callback_data=f'userwork_like {self.page_type} {0}'))
        return [buttons]

    def like_userwork(self, work_id):
        with session_scope() as db_sess:
            user = db_sess.query(User).filter(User.telegram_id == self.user_id).first()
            userwork = db_sess.merge(self.current_work)
            if user in userwork.users_liked:
                userwork.users_liked.remove(user)
            else:
                userwork.users_liked.append(user)
            db_sess.commit()
        # self._session.expire_all()
        self.current_work = self.get_userwork_func()
        self.update()


class PrivateUserWorksPageViewer(UserWorksViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'private_userworks', self.get_userworks, self.messages_handler,
                         self.generate_buttons)

        self.work_id_to_delete = None
        self.confirmation_message = None
        self.is_approved = None
        self.mode_picker_id = None

    def messages_handler(self, message):
        if message == 'nothing_found':
            return messages["no_private_userworks_found"]
        elif message == 'userworks_picker':
            if self.is_approved:
                return messages["approved_userworks_picker"]
            return messages["disapproved_userworks_picker"]
        elif message == 'page_text':
            return messages["private_userwork_page_element"]

    def show_works(self, is_approved):
        self.is_approved = is_approved
        super().show_works()

    def get_userworks(self):
        with session_scope() as session:
            works = list(session.query(UserWork).filter(and_(UserWork.user_id == self.user_id,
                                                             self.is_approved == UserWork.is_approved)))

        if not works:
            return []

        self.pages_amount = len(works)
        return works[self.current_page % self.pages_amount]

    def generate_buttons(self):
        if self.is_approved:
            return self.get_like_buttons()
        else:
            return [[types.InlineKeyboardButton(f'❌ ', callback_data=f'delete_private_userwork {0}')]]

    def send_delete_confirmation(self, work_id):
        self.work_id_to_delete = work_id
        markup = types.InlineKeyboardMarkup()

        markup.add(types.InlineKeyboardButton('Подтвердить', callback_data='delete_private_userwork_confirm'),
                   types.InlineKeyboardButton('Отмена', callback_data='delete_private_userwork_decline'))

        self.confirmation_message = self.bot.send_message(self.user_id, messages['delete_confirmation'],
                                                          reply_markup=markup).message_id

    def delete_userwork(self):
        with session_scope() as session:
            session.query(UserWork).filter(UserWork.id == self.current_work.id).delete()
            session.commit()

        self.update()
        self.delete_confirmation_message()

    def delete_confirmation_message(self):
        self.bot.delete_message(self.user_id, self.confirmation_message)
        self.confirmation_message = None
        self.work_id_to_delete = None

    def send_mode_picker(self):
        self.mode_picker_id = self.bot.send_message(self.user_id, "Мои работы:",
                                                    reply_markup=self.mode_picker_buttons()).message_id

    def mode_picker_buttons(self):
        markup = types.InlineKeyboardMarkup()

        markup.add(types.InlineKeyboardButton('Одобренные', callback_data=f'my_works approved'),
                   types.InlineKeyboardButton('На модерации', callback_data=f'my_works disapproved'))
        return markup


class UserWorksPageViewer(UserWorksViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'userworks', self.get_userwork, self.messages_handler, self.get_like_buttons)
        self.challenge_id = None

    def show_works(self, challenge_id):
        self.challenge_id = challenge_id
        super().show_works()

    def get_userwork(self):
        with session_scope() as session:
            works = list(session.query(UserWork).filter(
                and_(UserWork.is_approved, UserWork.challenge_id == self.challenge_id)))

        if not works:
            return []

        self.pages_amount = len(works)
        return works[self.current_page % self.pages_amount]

    def messages_handler(self, message):
        if message == 'nothing_found':
            return messages["no_userworks_found"]
        elif message == 'userworks_picker':
            return messages["userworks_picker"]
        elif message == 'page_text':
            return messages["userwork_page_element"]


class AdminUserWorksPageViewer(UserWorksViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'userworks', self.get_userwork, self.messages_handler, self.generate_buttons)

    def show_works(self):
        super().show_works()

    def get_userwork(self):
        with session_scope() as session:
            works = list(session.query(UserWork).filter(not_(UserWork.is_approved)))

        if not works:
            return []

        return works[self.current_page % len(works)]

    def messages_handler(self, message):
        if message == 'nothing_found':
            return messages["no_userworks_found"]
        elif message == 'userworks_picker':
            return 'Опции'
        elif message == 'page_text':
            with session_scope() as session:
                current_work = session.query(UserWork).filter(UserWork.id == self.current_work.id).one()
                return f'Челлендж {current_work.challenge.name}\nЮзер {current_work.user.name}'

    def generate_buttons(self):
        return [[
            types.InlineKeyboardButton('approve', callback_data=f'approve_userwork {self.current_work.id}'),
            types.InlineKeyboardButton('disapprove', callback_data=f'disapprove_userwork {self.current_work.id}')
        ]]

    def remove_userwork(self):
        userwork = self.current_work
        with session_scope() as session:
            session.query(UserWork).filter(UserWork.id == userwork.id).delete()
            session.commit()

    def approve_userwork(self):
        with session_scope() as session:
            userwork = session.query(UserWork).filter(UserWork.id == self.current_work.id).one()
            user = userwork.user
            challenge = userwork.challenge

            if challenge.is_hard:
                hard_userworks_messager.add_hard_userwork(userwork)

            self.give_prize(user, challenge)
            print(f'gave prize to user {user.name} {challenge.coins_prize}')
            userwork.is_approved = True
            session.commit()

    def give_prize(self, user, challenge):
        if challenge.is_hard:
            # prize is real
            print('CURRENTLY NO ACTUAL PRIZE IS ASSIGNED TO USER!!')
            pass
        else:
            user.coins += challenge.coins_prize
