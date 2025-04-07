from sqlalchemy import and_
from telebot import types
from db_data import models
from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User, Brand
from telebot.apihelper import ApiTelegramException


class ModeratorPromocodeViewer:
    def __init__(self, bot, admin_id, notify):
        self.bot = bot
        self.admin_id = admin_id
        self.notify = notify

        self.current_promocode_id = 0
        self.message_id = None

    def reset(self):
        self.current_promocode_id = 0

    def delete(self):
        if self.message_id:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.message_id = None

    def send_promocodes(self):
        self.reset()
        self.message_id = self.bot.send_message(self.admin_id, self.get_text(), reply_markup=self.get_markup()).message_id
        # promocode = self.get_promocode()
        # if promocode:
        #     self.message_id = self.bot.send_message(
        #         self.admin_id,
        #         self.get_text(),
        #         reply_markup=self.get_markup()
        #     ).message_id
        # else:
        #     self.message_id = self.bot.send_message(
        #         self.admin_id,
        #         'Нет промокодов'
        #     ).message_id

    def update(self):
        try:
            self.bot.edit_message_text(chat_id=self.admin_id, message_id=self.message_id, text=self.get_text(), reply_markup=self.get_markup())
        except ApiTelegramException:
            pass

    def get_text(self):
        promocode = self.get_promocode()
        if not promocode:
            return 'Нет промокодов'

        with session_scope() as session:
            promocode_obj = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.id == promocode.id).one()
            return f'@{promocode_obj.user.telegram_username} использовал промокод {promocode_obj.promocode.promo}'



    def next_page(self):
        self.current_promocode_id += 1
        self.update()

    def prev_page(self):
        self.current_promocode_id -= 1
        self.update()

    def get_markup(self):
        if not self.get_promocode():
            return types.InlineKeyboardMarkup()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('←', callback_data=f'prev_page promocodes'),
                   types.InlineKeyboardButton('→', callback_data=f'next_page promocodes'))
        markup.add(
            types.InlineKeyboardButton('Approve',
                                       callback_data=f'promo_confirmation approve'),
            types.InlineKeyboardButton('Decline', callback_data=f'promo_confirmation decline')
        )
        return markup

    def get_promocode(self):
        with session_scope() as session:
            promocodes = session.query(PromocodeOnModeration).all()

            if not promocodes:
                return []

            self.current_promocode_id %= len(promocodes)
            return promocodes[self.current_promocode_id]

    def approve(self):
        promo = self.get_promocode()
        with session_scope() as session:
            promocode = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.id == promo.id).one()
            promocode.user.used_promocodes.append(promocode.promocode)

            if promocode.promocode.coins != 0:
                promocode.user.coins += promocode.promocode.coins
                self.notify.balance_update(promocode.user.telegram_id, 'promocode_add_coins', promocode.promocode.coins)

            session.commit()

        self.delete_unauth_promocode()

    def disapprove(self):
        # TODO: send message to user that his promo was declined

        self.delete_unauth_promocode()

    def delete_unauth_promocode(self):
        promo_buf = self.get_promocode()
        with session_scope() as session:
            promo = session.query(PromocodeOnModeration).filter(and_(PromocodeOnModeration.promocode_id == promo_buf.promocode_id,
                                                                     PromocodeOnModeration.user_id == promo_buf.user_id)).one()
            session.delete(promo)
            session.commit()

        self.update()


class PromocodeViewer:
    def __init__(self, bot, admin_id, chainer):
        self.bot = bot
        self.admin_id = admin_id
        self.chainer = chainer

        self.current_promocode = None
        self.current_page = 0

        self.message_id = None
        self.edit_message_id = None

    def send_page(self):
        self.update_promocode()
        self.message_id = self.bot.send_message(self.admin_id, self.get_text(), reply_markup=self.get_markup()).message_id

    def update_page(self):
        self.update_promocode()
        try:
            self.bot.edit_message_text(chat_id=self.admin_id, message_id=self.message_id, text=self.get_text(), reply_markup=self.get_markup())
        except ApiTelegramException:
            pass

    def next_page(self):
        self.current_page += 1
        self.update_page()

    def prev_page(self):
        self.current_page -= 1
        self.update_page()

    def update_promocode(self):
        with session_scope() as db_sess:
            promocodes = db_sess.query(Promocode).all()

            if not promocodes:
                self.current_promocode = None
            else:
                self.current_promocode = promocodes[-(self.current_page % len(promocodes)) - 1]

    def send_edit_message(self):
        self.edit_message_id = self.bot.send_message(self.admin_id, 'Что изменить?', reply_markup=self.edit_message_markup()).message_id

    def edit_field(self, data):
        option = data.split('_')[1]
        def __edit_field(answer):
            value = answer[0]
            with session_scope() as session:
                promocode = session.query(Promocode).filter(Promocode.id == self.current_promocode.id).one()
                if option == 'promo':
                    promocode.promo = value
                elif option == 'coins':
                    promocode.coins = int(value)
                elif option == 'contact':
                    promocode.telegram_contact = value
                session.commit()
            self.chainer.clear_chain()
            self.update_page()

        if self.edit_message_id:
            self.bot.delete_message(chat_id=self.admin_id, message_id=self.edit_message_id)
            self.edit_message_id = None

        if option == 'promo':
            self.chainer.chain(['Введите новое название промокода'], [__edit_field])
        elif option == 'coins':
            self.chainer.chain(['Введите новое количество монет для вознаграждения'], [__edit_field])
        elif option == 'contact':
            self.chainer.chain(['Введите новый контакт (юзернейм в тг без @) (сейчас не юзается нигде)'], [__edit_field])

    def edit_message_markup(self):
        buttons = {'Название (сам промокод)': 'promo',
                   'Монетки': 'coins',
                   'Контакт': 'contact'}

        markup = types.InlineKeyboardMarkup()
        for key, value in buttons.items():
            markup.add(types.InlineKeyboardButton(key, callback_data=f'promocode_viewer edit_{value}'))
        return markup

    def add_promocode(self):
        silly_name = 'ChangeOrWillBeDeleted'

        with session_scope() as session:
            session.query(Promocode).filter(Promocode.promo == silly_name).delete()

            promocode = Promocode(
                brand=Brand(),
                promo=silly_name,
                coins=0,
                need_confirmation=False,
                is_expired=True
            )
            session.add(promocode)
            session.commit()
        self.current_page = 0
        self.update_page()

    def change_is_expired(self):
        with session_scope() as session:
            promocode = session.query(Promocode).filter(Promocode.id == self.current_promocode.id).one()
            promocode.is_expired = not promocode.is_expired
            session.commit()
        self.update_page()

    def change_need_confirmation(self):
        with session_scope() as session:
            promocode = session.query(Promocode).filter(Promocode.id == self.current_promocode.id).one()
            promocode.need_confirmation = not promocode.need_confirmation
            session.commit()
        self.update_page()

    def get_text(self):
        if self.current_promocode:
            return (f"{self.current_promocode.promo}\n"
                    f"Монетки: {self.current_promocode.coins}\n"
                    f"Контакт: @{self.current_promocode.telegram_contact}\n"
                    f"Надо подтверждать? {'ДА' if self.current_promocode.need_confirmation else 'НЕТ'}\n"
                    f"Активный? {'ДА' if not self.current_promocode.is_expired else 'НЕТ'}")
        else:
            return 'Нет промокодов'

    def get_markup(self):
        markup = types.InlineKeyboardMarkup()
        if not self.current_promocode:
            markup.add(types.InlineKeyboardButton('Создать промокод', callback_data=f'promocode_viewer add_promocode'))
            return markup

        markup.add(types.InlineKeyboardButton('Поменять активность', callback_data=f'promocode_viewer change_is_expired'),
                   types.InlineKeyboardButton('Поменять подтверждение', callback_data=f'promocode_viewer change_need_confirmation'))

        markup.add(types.InlineKeyboardButton('Изменить другие поля', callback_data=f'promocode_viewer edit'))

        markup.add(types.InlineKeyboardButton('←', callback_data=f'promocode_viewer prev_page'),
                   types.InlineKeyboardButton('→', callback_data=f'promocode_viewer next_page'))
        markup.add(types.InlineKeyboardButton('Создать промокод', callback_data=f'promocode_viewer add_promocode'))

        return markup
