from telebot import types
from db_data import models
from db_data.db_session import session_scope, create_session
from db_data.models import UnauthorizedPromocode


class PromocodeViewer:
    def __init__(self, bot, admin_id):
        self.bot = bot
        self.admin_id = admin_id
        self.current_promocode_id = 0
        self.message_id = None
        self._session = create_session()

    def reset(self):
        self.current_promocode_id = 0

    def delete(self):
        if self.message_id:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.message_id = None

    def send_promocodes(self):
        self.reset()
        promocode = self.get_promocode()
        if promocode:
            self.message_id = self.bot.send_message(
                self.admin_id,
                f'@{promocode.username} '
                f'использовал промокод: {promocode.promocode.promo}',
                reply_markup=self.get_markup()
            ).message_id
        else:
            self.message_id = self.bot.send_message(
                self.admin_id,
                'Нет промокодов'
            ).message_id

    def update(self):
        promocode = self.get_promocode()
        try:
            if promocode:
                self.bot.edit_message_text(
                    chat_id=self.admin_id,
                    message_id=self.message_id,
                    text=f'@{promocode.username} '
                    f'использовал промокод: {promocode.promocode.promo}',
                    reply_markup=self.get_markup()
                )
            else:
                self.bot.edit_message_text(
                    chat_id=self.admin_id,
                    message_id=self.message_id,
                    text='Нет промокодов',
                )
        except Exception as e:
            # print(e)
            pass

    def next_page(self):
        self.current_promocode_id += 1
        self.update()

    def prev_page(self):
        self.current_promocode_id -= 1
        self.update()

    def get_markup(self):
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
        promocodes = self._session.query(UnauthorizedPromocode).all()
        if not promocodes:
            return []

        self.current_promocode_id %= len(promocodes)
        return promocodes[self.current_promocode_id]

    def approve(self):
        promo = self.get_promocode()
        promo.user.used_promocodes.append(promo.promocode)
        self._session.delete(promo)
        self._session.commit()
        self.update()

    def disapprove(self):
        promo = self.get_promocode()
        self._session.delete(promo)
        self._session.commit()
        self.update()
