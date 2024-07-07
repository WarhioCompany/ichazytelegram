from db_data.db_session import session_scope, create_session
from db_data.models import User, UserWork
from telebot import types
from messages_handler import messages
from sqlalchemy import and_, not_

from page_viewer.page_viewer import PageViewer


class UserWorksViewer(PageViewer):
    def __init__(self, bot, user_id, identifier, get_userworks_func, messages_handler, buttons_generator):
        super().__init__(bot, user_id)

        self.works_on_page = 3
        self.current_works = []
        self.userworks = []

        self.identifier = identifier
        self.get_userworks_func = get_userworks_func
        self.messages_handler = messages_handler
        self.buttons_generator = buttons_generator

        self._session = None

    def show_works(self, *args):
        self._session = create_session()

        # TJLAKJSD

        self.current_works = self.get_userworks_func()
        if self.current_works:
            self.send_page(self.get_media_group())
            self.send_picker(self.messages_handler("userworks_picker"), self.get_buttons())
        else:
            self.reset()
            self.send_picker(self.messages_handler('nothing_found'))

    def get_media_group(self):
        media = []
        for work in self.current_works:
            if work.type == 'video':
                media.append(types.InputMediaVideo(work.data))
            elif work.type == 'image':
                media.append(types.InputMediaPhoto(work.data))
        media[0].caption = self.works_page_text()
        return media

    def next_page(self):
        self.current_page += 1
        self.update()

    def prev_page(self):
        if self.current_page != 0:
            self.current_page -= 1
            self.update()

    def update(self):
        self.current_works = self.get_userworks_func()

        if self.current_works:
            self.update_page(self.get_media_group())
            self.update_picker(self.messages_handler("userworks_picker"), self.get_buttons())
        else:
            self.reset()
            self.send_picker(self.messages_handler('nothing_found'))

    def works_page_text(self):
        return '\n'.join(self.messages_handler('page_text').format(
            id=i + 1,
            username=self.current_works[i].user.name,
            challenge=self.current_works[i].challenge.name
        ) for i in range(len(self.current_works)))

    def like_userwork(self, work_id):
        with session_scope() as db_sess:
            user = db_sess.query(User).filter(User.telegram_id == self.user_id).first()
            userwork = db_sess.merge(self.current_works[work_id])
            if user in userwork.users_liked:
                userwork.users_liked.remove(user)
            else:
                userwork.users_liked.append(user)
            db_sess.commit()
        self._session.expire_all()
        self.current_works = self.get_userworks_func()
        self.update_picker(self.messages_handler("userworks_picker"), self.get_buttons())

    def get_buttons(self):
        markup = types.InlineKeyboardMarkup()

        # markup.add(*[types.InlineKeyboardButton(f'{i + 1}: {likes[i]}🤍', callback_data=f'userwork_like {i}')
        #              for i in range(len(self.current_works))])
        if self.buttons_generator:
            buttons = self.buttons_generator()
            for row in buttons:
                markup.add(*row)

        markup.add(types.InlineKeyboardButton('⬅', callback_data=f'prev_page {self.identifier}'),
                   types.InlineKeyboardButton('➡', callback_data=f'next_page {self.identifier}'))
        return markup

    def does_exist(self):
        return bool(self.picker_id)

    def get_like_buttons(self):
        buttons = []
        user_dummy = User(telegram_id=f'{self.user_id}')
        # ❤ 🤍
        for i in range(len(self.current_works)):
            if user_dummy in self.current_works[i].users_liked:
                s = f'{i + 1}: {len(self.current_works[i].users_liked)}❤'
            else:
                s = f'{i + 1}: {len(self.current_works[i].users_liked)}🤍'
            buttons.append(types.InlineKeyboardButton(s, callback_data=f'userwork_like {self.identifier} {i}'))
        return [buttons]


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
        works = list(self._session.query(UserWork).filter(and_(UserWork.user_id == self.user_id,
                                                               self.is_approved == UserWork.is_approved)))
        if not works:
            return []

        res = []
        for i in range(self.works_on_page):
            work_id = (self.current_page * self.works_on_page + i) % len(works)
            res.append(works[work_id])
        return res

    def generate_buttons(self):
        if self.is_approved:
            return self.get_like_buttons()
        else:
            return [[types.InlineKeyboardButton(f'{i + 1}: ❌ ', callback_data=f'delete_private_userwork {i}')
                     for i in range(self.works_on_page)]]

    def send_delete_confirmation(self, work_id):
        self.work_id_to_delete = work_id
        markup = types.InlineKeyboardMarkup()

        markup.add(types.InlineKeyboardButton('Подтвердить', callback_data='delete_private_userwork_confirm'),
                   types.InlineKeyboardButton('Отмена', callback_data='delete_private_userwork_decline'))

        self.confirmation_message = self.bot.send_message(self.user_id, messages['delete_confirmation'],
                                                          reply_markup=markup).message_id

    def delete_userwork(self):
        self._session.query(UserWork).filter(UserWork.id == self.current_works[self.work_id_to_delete].id).delete()
        self._session.commit()
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
                   types.InlineKeyboardButton('Неодобренные', callback_data=f'my_works disapproved'))
        return markup


class UserWorksPageViewer(UserWorksViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'userworks', self.get_userworks, self.messages_handler, self.get_like_buttons)
        self.challenge_id = None

    def show_works(self, challenge_id):
        self.challenge_id = challenge_id
        super().show_works()

    def get_userworks(self):
        works = list(self._session.query(UserWork).filter(
            and_(UserWork.is_approved, UserWork.challenge_id == self.challenge_id)))
        if not works:
            return []

        res = []
        for i in range(self.works_on_page):
            work_id = (self.current_page * self.works_on_page + i) % len(works)
            res.append(works[work_id])
        return res

    def messages_handler(self, message):
        if message == 'nothing_found':
            return messages["no_userworks_found"]
        elif message == 'userworks_picker':
            return messages["userworks_picker"]
        elif message == 'page_text':
            return messages["userwork_page_element"]


class AdminUserWorksPageViewer(UserWorksViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'userworks', self.get_userworks, self.messages_handler, self.generate_buttons)
        self.works_on_page = 1

    def show_works(self):
        super().show_works()

    def get_userworks(self):
        works = list(self._session.query(UserWork).filter(not_(UserWork.is_approved)))
        if not works:
            return []

        res = []
        for i in range(self.works_on_page):
            work_id = (self.current_page * self.works_on_page + i) % len(works)
            res.append(works[work_id])
        return res

    def messages_handler(self, message):
        if message == 'nothing_found':
            return messages["no_userworks_found"]
        elif message == 'userworks_picker':
            return 'Опции'
        elif message == 'page_text':
            return self.current_works[0].challenge.name

    def generate_buttons(self):
        return [[
            types.InlineKeyboardButton('approve', callback_data=f'approve_userwork {self.current_works[0].id}'),
            types.InlineKeyboardButton('disapprove', callback_data=f'disapprove_userwork {self.current_works[0].id}')
        ]]

    def remove_userwork(self):
        userwork = self.current_works[0]
        self._session.query(UserWork).filter(UserWork.id == userwork.id).delete()

        self._session.commit()

    def approve_userwork(self):
        with session_scope() as session:
            userwork = session.query(UserWork).filter(UserWork.id == self.current_works[0].id).one()
            user = userwork.user
            challenge = userwork.challenge

            self.give_prize(user, challenge)
            print(f'gave prize to user {user.name} {challenge.coins_prize}')
            userwork.is_approved = True
            session.commit()

    def give_prize(self, user, challenge):
        if challenge.is_hard:
            # prize is real
            pass
        else:
            user.coins += challenge.coins_prize
