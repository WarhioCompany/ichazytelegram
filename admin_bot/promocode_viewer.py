from telebot import types
from db_data import models
from db_data.db_session import session_scope
from db_data.models import UnauthorizedPromocode


class PromocodeViewer:
    def __init__(self, bot, admin_id):
        self.bot = bot
        self.admin_id = admin_id
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
        promocode = self.get_promocode()
        if promocode:
            self.message_id = self.bot.send_message(
                self.admin_id,
                f'@{promocode["username"]} '
                f'использовал промокод: {promocode["promocode_string"]}',
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
                    text=f'@{promocode["username"]} '
                    f'использовал промокод: {promocode["promocode_string"]}',
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
        with session_scope() as session:
            promocodes = session.query(UnauthorizedPromocode).all()

            if not promocodes:
                return []

            self.current_promocode_id %= len(promocodes)
            promocode = promocodes[self.current_promocode_id]
            return {'username': promocode.username, 'promocode_string': promocode.promocode.promo, 'id': promocode.id}

    def approve(self):
        promo_buf = self.get_promocode()
        with session_scope() as session:
            promo = session.query(UnauthorizedPromocode).filter(UnauthorizedPromocode.id == promo_buf['id']).one()
            promo.user.used_promocodes.append(promo.promocode)

            session.commit()

        self.delete_unauth_promocode()

    def disapprove(self):
        self.delete_unauth_promocode()

    def delete_unauth_promocode(self):
        promo_buf = self.get_promocode()
        with session_scope() as session:
            promo = session.query(UnauthorizedPromocode).filter(UnauthorizedPromocode.id == promo_buf['id']).one()
            session.delete(promo)
            session.commit()

        self.update()