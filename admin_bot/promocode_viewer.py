from sqlalchemy import and_, not_
from telebot import types
from telebot.types import InputMediaPhoto

from db_data import models
from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User, Brand, BoostPromocode
from telebot.apihelper import ApiTelegramException
import promocode_tools


# View Promocode On Approval Queue
class ModeratorPromocodeViewer:
    def __init__(self, bot, admin_id, notify):
        self.bot = bot
        self.admin_id = admin_id
        self.notify = notify

        self.current_promocode_id = 0
        self.current_promocode = None
        self.message_id = None

    def reset(self):
        self.current_promocode_id = 0
        self.get_promocode()

    def delete(self):
        if self.message_id:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.message_id = None

    def send_promocodes(self):
        self.reset()
        if not self.current_promocode:
            self.message_id = self.bot.send_message(self.admin_id, 'Нечего модерировать').message_id
            return

        if self.current_promocode.image_proof:
            self.message_id = self.bot.send_photo(self.admin_id, self.current_promocode.image_proof, self.get_text(), reply_markup=self.get_markup()).message_id
        else:
            self.message_id = self.bot.send_message(self.admin_id, self.get_text(), reply_markup=self.get_markup()).message_id

    def update(self):
        self.get_promocode()
        try:
            if self.current_promocode.image_proof:
                self.bot.edit_message_media(chat_id=self.admin_id, message_id=self.message_id, media=self.get_media(), reply_markup=self.get_markup())
            else:
                self.update_text_only_promocode()

        except ApiTelegramException as e:
            print(e)

    def update_text_only_promocode(self):
        try:
            self.bot.edit_message_text(chat_id=self.admin_id, message_id=self.message_id, text=self.get_text(),
                                       reply_markup=self.get_markup())
        except ApiTelegramException:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.message_id = self.bot.send_message(self.admin_id, self.get_text(),
                                                    reply_markup=self.get_markup()).message_id

    def get_media(self):
        return InputMediaPhoto(self.current_promocode.image_proof, caption=self.get_text())

    def get_text(self):
        if not self.current_promocode:
            return 'Нет промокодов'

        with session_scope() as session:
            promocode_obj = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.id == self.current_promocode.id).one()
            promo = promocode_obj.get_promocode().promo

            return f'@{promocode_obj.user.telegram_username} использовал промокод {promo}'


    def next_page(self):
        self.current_promocode_id += 1
        self.update()

    def prev_page(self):
        self.current_promocode_id -= 1
        self.update()

    def get_markup(self):
        if not self.current_promocode:
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
            promocodes = list(session.query(PromocodeOnModeration).all())

            if not promocodes:
                self.current_promocode = None
            else:
                self.current_promocode_id %= len(promocodes)
                self.current_promocode = promocodes[self.current_promocode_id]

    def approve(self):
        if self.current_promocode.promocode_type == 'coins':
            promocode_tools.use_promocode(self.current_promocode.promocode_id, self.current_promocode.user_id, self.notify)
        else:
            promocode_tools.use_boost_promocode(self.current_promocode.promocode_id, self.current_promocode.user_id, self.notify)

        self.delete_promocode()

    def disapprove(self):
        # TODO: send message to user that his promo was declined

        self.delete_promocode()

    def delete_promocode(self):
        with session_scope() as session:
            promo = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.id == self.current_promocode.id).one()
            session.delete(promo)
            session.commit()

        self.update()



